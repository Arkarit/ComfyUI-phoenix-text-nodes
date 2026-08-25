import re

COMMENT_LINE_PATTERN = re.compile(r"^\s*#")


class PhoenixFilterComments:
    DESCRIPTION = (
        "Removes comment lines from the input text entirely, so they "
        "never reach whatever comes next (e.g. a normal CLIP Text "
        "Encode). A line is a comment if it starts with # (leading "
        "whitespace is ignored); every other line passes through "
        "unchanged."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "forceInput": True, "multiline": True,
                    "tooltip": "The input text. Lines starting with # (leading whitespace ignored) are removed entirely.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "phoenix/text"

    def run(self, text):
        lines = [line for line in text.splitlines() if not COMMENT_LINE_PATTERN.match(line)]
        return ("\n".join(lines),)


NODE_CLASS_MAPPINGS = {
    "PhoenixFilterComments": PhoenixFilterComments,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixFilterComments": "🧹 Filter Comments (Phoenix)",
}
