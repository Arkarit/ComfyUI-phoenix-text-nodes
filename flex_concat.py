MAX_INPUTS = 100


class PhoenixFlexConcat:
    DESCRIPTION = (
        "Concatenates any number of connected values into one text string. "
        "'count' (1-100) sets how many input sockets the node shows on "
        "screen — a frontend extension adds/removes them to match. Each "
        "socket is optional and typeless, so anything can be connected "
        "(e.g. a seed INT), and its value is converted to text and joined "
        "with 'delimiter' in socket order."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "count": ("INT", {
                    "default": 2, "min": 1, "max": MAX_INPUTS, "step": 1,
                    "tooltip": "Number of concat input sockets shown on the node.",
                }),
                "delimiter": ("STRING", {
                    "default": ", ",
                    "tooltip": "Text inserted between each connected input's value.",
                }),
            },
            "optional": {
                f"input_{i}": ("*", {
                    "tooltip": "Any value. Converted to text and joined in socket order.",
                })
                for i in range(1, MAX_INPUTS + 1)
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "phoenix/text"

    def run(self, count, delimiter, **kwargs):
        parts = []
        for i in range(1, count + 1):
            value = kwargs.get(f"input_{i}")
            if value is None:
                continue
            parts.append(value if isinstance(value, str) else str(value))
        return (delimiter.join(parts),)


NODE_CLASS_MAPPINGS = {
    "PhoenixFlexConcat": PhoenixFlexConcat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixFlexConcat": "🔗 Flex Concat (Phoenix)",
}
