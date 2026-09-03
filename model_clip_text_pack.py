from .model_clip_text import MODEL_CLIP_TEXT_TYPE, build_struct


class PhoenixModelClipTextPack:
    DESCRIPTION = (
        "Packs model, clip and an optional starting keywords text into a "
        "model_clip_text struct. See this node's Info tab (Properties Panel) "
        "for full details."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "model": ("MODEL", {
                    "tooltip": "The diffusion model to pack.",
                }),
                "clip": ("CLIP", {
                    "tooltip": "The CLIP model to pack.",
                }),
                "keywords": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Optional starting keywords, e.g. a base style prompt, before any LoRA adds its own.",
                }),
            },
        }

    RETURN_TYPES = (MODEL_CLIP_TEXT_TYPE,)
    RETURN_NAMES = ("model_clip_text",)
    FUNCTION = "pack"
    CATEGORY = "phoenix/loaders"

    def pack(self, model=None, clip=None, keywords=""):
        return (build_struct(model, clip, keywords),)


NODE_CLASS_MAPPINGS = {
    "PhoenixModelClipTextPack": PhoenixModelClipTextPack,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixModelClipTextPack": "📦 Pack Model/Clip/Text (Phoenix)",
}
