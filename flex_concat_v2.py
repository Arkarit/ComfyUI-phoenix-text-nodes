import re

MAX_INPUTS = 100


class PhoenixFlexConcatV2:
    DESCRIPTION = (
        "Inserts any number of connected values into a text template "
        "using $1, $2, ... placeholders (or joins them with newlines if "
        "the template is empty). See this node's Info tab (Properties "
        "Panel) for full details."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "count": ("INT", {
                    "default": 2, "min": 1, "max": MAX_INPUTS, "step": 1,
                    "tooltip": "Number of concat input sockets shown on the node.",
                }),
                "text": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Template containing the placeholders to be replaced. If left completely empty, the connected values are joined with newlines instead.",
                }),
                "search_string": ("STRING", {
                    "default": "$",
                    "tooltip": 'Prefix before the placeholder index, e.g. "$" makes placeholders $1, $2, ... (always starting at 1).',
                }),
            },
            "optional": {
                f"input_{i}": ("*", {
                    "tooltip": "Any value. Converted to text and substituted for its placeholder in socket order.",
                })
                for i in range(1, MAX_INPUTS + 1)
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "phoenix/text"

    def run(self, count, text, search_string, **kwargs):
        values = []
        for i in range(1, count + 1):
            value = kwargs.get(f"input_{i}")
            if value is None:
                continue
            values.append((i, value if isinstance(value, str) else str(value)))

        if text == "":
            return ("\n".join(value for _, value in values),)

        replacements = dict(values)
        # Match complete indices once; inserted values remain literal.
        pattern = re.compile(re.escape(search_string) + r"(\d+)")
        result = pattern.sub(
            lambda match: replacements.get(int(match.group(1)), match.group(0)), text
        )
        return (result,)


NODE_CLASS_MAPPINGS = {
    "PhoenixFlexConcatV2": PhoenixFlexConcatV2,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixFlexConcatV2": "🔗 Flex Concat (Phoenix) V2",
}
