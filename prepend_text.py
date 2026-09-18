SEPARATORS = {
    "none": "",
    "newline": "\n",
    "blank line": "\n\n",
    "space": " ",
}

SEPARATOR_TOOLTIP = (
    "Separator inserted between the two parts. Only inserted when both "
    "parts are non-empty. Default 'none' concatenates directly."
)


class PhoenixPrependText:
    DESCRIPTION = (
        "Prepends a fixed string to the start of the input text, optionally "
        "with a separator. See this node's Info tab (Properties Panel) for "
        "full details."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "forceInput": True, "multiline": True,
                    "tooltip": "The input text.",
                }),
                "prepend": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Text prepended to the start of the input.",
                }),
                "separator": (list(SEPARATORS), {
                    "default": "none",
                    "tooltip": SEPARATOR_TOOLTIP,
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "phoenix/text"

    def run(self, text, prepend, separator="none"):
        sep = SEPARATORS.get(separator, "") if (prepend and text) else ""
        return (prepend + sep + text,)


NODE_CLASS_MAPPINGS = {
    "PhoenixPrependText": PhoenixPrependText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixPrependText": "➕ Prepend Text (Phoenix)",
}
