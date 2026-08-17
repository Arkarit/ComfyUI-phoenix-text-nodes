import csv
import io
import random

UNIQUE_KEYWORD = "_UNIQUE_"
NONE_KEYWORD = "_NONE_"


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
    "_NONE_" behind."""

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
        "entirely instead of substituting a term. Shows the result in a "
        "read-only preview widget on the node itself."
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
                        "substituting a term."
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
                pool = candidates
                if row_unique:
                    remaining = [c for c in candidates if c not in used]
                    if remaining:
                        pool = remaining

                choice = rng.choice(pool)
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
