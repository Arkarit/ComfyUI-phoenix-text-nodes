import csv
import io
import random
import re

UNIQUE_KEYWORD = "_UNIQUE_"
NONE_KEYWORD = "_NONE_"
WEIGHT_PATTERN = re.compile(r"_(\d+(?:\.\d+)?)_")


def _parse_weight(candidate):
    """Splits a candidate like "_2_ green" into ("green", 2.0). A candidate
    without a _NUMBER_ token gets weight 1.0. A weight token placed before a
    quoted field (e.g. _100_ "") defeats CSV's own quote parsing, since a
    quote is only special at the very start of a field, so the leftover
    text is unquoted here instead, letting _100_ "" mean an empty string
    with weight 100 rather than the literal two-character text ""."""
    match = WEIGHT_PATTERN.search(candidate)
    if not match:
        return candidate, 1.0
    text = (candidate[:match.start()] + candidate[match.end():]).strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    return text, float(match.group(1))


class PhoenixRandomCSVTextReplace:
    """Replaces sequential placeholders (search_string + index) in a text
    with a random term picked from a per-placeholder candidate list. The
    candidate lists are given as CSV: each row is one placeholder's
    candidates, row order maps to start_index, start_index+1, ... — so any
    number of placeholders is supported, and quoted fields let a candidate
    contain a comma. start_index also lets you chain several of these
    nodes to cover a larger range. Same seed + same terms always picks the
    same term. A placeholder whose row is missing or empty is left
    unchanged.

    Rows are independent by default, so the same term can be picked for
    more than one placeholder. Set 'unique' to make every row avoid terms
    already picked by another unique row this run, or mark only specific
    rows by adding the literal field _UNIQUE_ to that row's CSV — it's
    stripped out before picking, it isn't itself a candidate. If a unique
    row's candidates are all already taken, it falls back to picking from
    the full list rather than leaving the placeholder unresolved.

    A row whose only field is _NONE_ removes its placeholder from the
    output entirely instead of substituting a term — e.g. row 5
    containing just _NONE_ deletes $5 rather than leaving "$5" or
    "_NONE_" behind.

    A candidate may contain a _NUMBER_ token (e.g. "_2_ green") to weight
    how often it's picked relative to the row's other candidates (default
    weight 1); the token is stripped from the term before use. E.g. for
    "red, _2_ green, _0.1_ blue", green comes up twice as often as red,
    and blue only a tenth as often as red."""

    DESCRIPTION = (
        "Replaces sequential placeholders (search_string + index, e.g. "
        "$1, $2, ...) in a text with a random term picked from a "
        "per-placeholder candidate list. terms is CSV: each row is one "
        "placeholder's comma-separated candidates (quote a field to "
        "include a literal comma), row order maps to start_index, "
        "start_index+1, ... — any number of rows/placeholders is "
        "supported. start_index also lets you chain several of these "
        "nodes to cover a larger range, e.g. one node covering $1-$5, a "
        "second with start_index=6 covering $6-$10. Same seed + same "
        "terms always picks the same term. A placeholder whose row is "
        "missing or empty is left unchanged. Rows are independent by "
        "default (the same term can come up more than once); enable "
        "'unique' to forbid that across all rows, or add the literal "
        "field _UNIQUE_ to only specific CSV rows to opt just those in — "
        "the keyword itself is removed before picking, not a candidate. "
        "If a unique row's candidates are all already used, it falls "
        "back to the full list instead of failing. A row whose only "
        "field is _NONE_ removes its placeholder from the output "
        "entirely instead of substituting a term. A candidate may "
        "contain a _NUMBER_ token (e.g. \"_2_ green\") to weight how "
        "often it's picked relative to the row's other candidates "
        "(default weight 1); the token is stripped from the term before "
        "use. Shows the result in a read-only preview widget on the "
        "node itself."
    )
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "A $1 riding a $2 through $3.",
                    "tooltip": "Text containing the placeholders to be replaced.",
                }),
                "search_string": ("STRING", {
                    "multiline": False, "default": "$",
                    "tooltip": 'Prefix before the placeholder index, e.g. "$" makes placeholders $1, $2, ...',
                }),
                "start_index": ("INT", {
                    "default": 1, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "First placeholder index. Chain multiple nodes by offsetting this, e.g. 1 then 6 for $1-$5 and $6-$10.",
                }),
                "terms": ("STRING", {
                    "multiline": True,
                    "default": 'goose,wizard,astronaut\nmoped,unicycle,tank\n"a forest, at night",downtown,the moon',
                    "tooltip": (
                        "CSV: one row per placeholder, row order = start_index, start_index+1, ... "
                        "Any number of rows/columns. Quote a field to include a literal comma, e.g. \"a, b\",c. "
                        "Add the field _UNIQUE_ to a row to make just that row avoid terms already picked by "
                        "another unique row this run (it's removed before picking, not a candidate itself). "
                        "A row containing only _NONE_ removes its placeholder from the output instead of "
                        "substituting a term. Add a _NUMBER_ token to a candidate, e.g. \"_2_ green\", to "
                        "weight how often it's picked relative to the row's other candidates (default 1); "
                        "the token is stripped from the term before use."
                    ),
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "Controls which term is picked. Same seed + same terms always gives the same result.",
                }),
                "unique": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "If enabled, every row avoids terms already picked by another row this run, so no term "
                        "is used twice. Off by default (rows are independent, terms can repeat). To make only "
                        "some rows unique instead of all, leave this off and add _UNIQUE_ to those rows' terms."
                    ),
                }),
            },
            "optional": {
                "preview": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Read-only preview of the last result. Not an input; updates after each run.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "replace"
    CATEGORY = "phoenix/text"

    def replace(self, text, search_string, start_index, terms, seed, unique=False, preview=""):
        rng = random.Random(seed)
        result = text
        used = set()
        rows = csv.reader(io.StringIO(terms), skipinitialspace=True)
        for offset, row in enumerate(rows):
            fields = [field.strip() for field in row if field.strip()]
            row_unique = unique or UNIQUE_KEYWORD in fields
            candidates = [f for f in fields if f != UNIQUE_KEYWORD]
            if not candidates:
                continue

            if candidates == [NONE_KEYWORD]:
                choice = ""
            else:
                weighted = [_parse_weight(c) for c in candidates]
                pool = weighted
                if row_unique:
                    remaining = [(t, w) for t, w in weighted if t not in used]
                    if remaining:
                        pool = remaining

                choice = rng.choices([t for t, _ in pool], weights=[w for _, w in pool], k=1)[0]
                if row_unique:
                    used.add(choice)

            placeholder = f"{search_string}{start_index + offset}"
            result = result.replace(placeholder, choice)
        return {"ui": {"text": [result]}, "result": (result,)}


NODE_CLASS_MAPPINGS = {
    "PhoenixRandomCSVTextReplace": PhoenixRandomCSVTextReplace,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixRandomCSVTextReplace": "Phoenix Random CSV Text Replace",
}
