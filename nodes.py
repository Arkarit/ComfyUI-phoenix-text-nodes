class PhoenixTextConcat:
    """Example node: concatenates two strings with a separator."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_a": ("STRING", {"multiline": True, "default": ""}),
                "text_b": ("STRING", {"multiline": True, "default": ""}),
                "separator": ("STRING", {"default": " "}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "phoenix/text"

    def run(self, text_a, text_b, separator):
        return (f"{text_a}{separator}{text_b}",)


NODE_CLASS_MAPPINGS = {
    "PhoenixTextConcat": PhoenixTextConcat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixTextConcat": "🔤 Text Concat (Phoenix)",
}
