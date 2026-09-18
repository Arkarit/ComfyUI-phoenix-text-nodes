from .prepend_text import SEPARATORS, SEPARATOR_TOOLTIP


class PhoenixAppendText:
    DESCRIPTION = (
        "Appends a fixed string to the end of the input text, optionally "
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
                "append": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Text appended to the end of the input.",
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

    def run(self, text, append, separator="none"):
        sep = SEPARATORS.get(separator, "") if (text and append) else ""
        return (text + sep + append,)


NODE_CLASS_MAPPINGS = {
    "PhoenixAppendText": PhoenixAppendText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixAppendText": "➕ Append Text (Phoenix)",
}
