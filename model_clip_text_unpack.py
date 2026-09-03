from .model_clip_text import MODEL_CLIP_TEXT_TYPE


class PhoenixModelClipTextUnpack:
    DESCRIPTION = (
        "Unpacks a model_clip_text struct back into model, clip and "
        "keywords. See this node's Info tab (Properties Panel) for full "
        "details."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_clip_text": (MODEL_CLIP_TEXT_TYPE, {
                    "tooltip": "The struct to unpack, from Pack Model/Clip/Text (Phoenix) or Load Lora (Phoenix).",
                }),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("model", "clip", "keywords")
    FUNCTION = "unpack"
    CATEGORY = "phoenix/loaders"

    def unpack(self, model_clip_text):
        keywords = model_clip_text.get("keywords") or ""
        if keywords:
            keywords += "\n"
        return (
            model_clip_text.get("model"),
            model_clip_text.get("clip"),
            keywords,
        )


NODE_CLASS_MAPPINGS = {
    "PhoenixModelClipTextUnpack": PhoenixModelClipTextUnpack,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixModelClipTextUnpack": "📤 Unpack Model/Clip/Text (Phoenix)",
}
