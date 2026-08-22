class PhoenixPrependText:
    DESCRIPTION = "Prepends a fixed string to the start of the input text."

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
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "phoenix/text"

    def run(self, text, prepend):
        return (prepend + text,)


NODE_CLASS_MAPPINGS = {
    "PhoenixPrependText": PhoenixPrependText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixPrependText": "➕ Prepend Text (Phoenix)",
}
