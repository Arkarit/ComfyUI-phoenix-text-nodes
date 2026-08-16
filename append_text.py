class PhoenixAppendText:
    DESCRIPTION = "Appends a fixed string to the end of the input text."

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
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "phoenix/text"

    def run(self, text, append):
        return (text + append,)


NODE_CLASS_MAPPINGS = {
    "PhoenixAppendText": PhoenixAppendText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixAppendText": "➕ Append Text (Phoenix)",
}
