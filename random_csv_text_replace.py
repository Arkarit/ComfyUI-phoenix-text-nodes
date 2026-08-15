import csv
import io
import random


class PhoenixRandomCSVTextReplace:
    """Replaces sequential placeholders (search_string + index) in a text
    with a random term picked from a per-placeholder candidate list. The
    candidate lists are given as CSV: each row is one placeholder's
    candidates, row order maps to start_index, start_index+1, ... — so any
    number of placeholders is supported, and quoted fields let a candidate
    contain a comma. start_index also lets you chain several of these
    nodes to cover a larger range. Same seed + same terms always picks the
    same term. A placeholder whose row is missing or empty is left
    unchanged."""

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
        "missing or empty is left unchanged. Shows the result in a "
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
                        "Any number of rows/columns. Quote a field to include a literal comma, e.g. \"a, b\",c."
                    ),
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "Controls which term is picked. Same seed + same terms always gives the same result.",
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

    def replace(self, text, search_string, start_index, terms, seed, preview=""):
        rng = random.Random(seed)
        result = text
        rows = csv.reader(io.StringIO(terms), skipinitialspace=True)
        for offset, row in enumerate(rows):
            candidates = [field.strip() for field in row if field.strip()]
            if candidates:
                placeholder = f"{search_string}{start_index + offset}"
                result = result.replace(placeholder, rng.choice(candidates))
        return {"ui": {"text": [result]}, "result": (result,)}


NODE_CLASS_MAPPINGS = {
    "PhoenixRandomCSVTextReplace": PhoenixRandomCSVTextReplace,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixRandomCSVTextReplace": "Phoenix Random CSV Text Replace",
}
