class PhoenixCarriageReturn:
    DESCRIPTION = "Outputs a string of 'number' newline characters, e.g. to join text pieces without a delimiter widget."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "number": ("INT", {
                    "default": 1, "min": 0, "max": 4096, "step": 1,
                    "tooltip": "How many newline characters to output.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "phoenix/text"

    def run(self, number):
        return ("\n" * number,)


NODE_CLASS_MAPPINGS = {
    "PhoenixCarriageReturn": PhoenixCarriageReturn,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixCarriageReturn": "↵ Carriage Return (Phoenix)",
}
