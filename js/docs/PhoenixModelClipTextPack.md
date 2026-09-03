# Phoenix Pack Model/Clip/Text

Packs `model`, `clip` (both optional) and an optional starting `keywords` text into a single `model_clip_text` struct — the same struct type produced and consumed by **Phoenix Load Lora**. Applies no LoRA; it's a pure "wrap these into a struct" node.

## Why it exists

**Phoenix Load Lora** only has a `model_clip_text` input — it has no separate `model`/`clip` sockets. This node is the on-ramp: place it right before the first **Phoenix Load Lora** in a chain, feeding a checkpoint loader's `model`/`clip` in and this node's `model_clip_text` output into that first LoRA node.

## Inputs

- `model` (optional) — passed straight through into the struct and as the plain `model` output.
- `clip` (optional) — same, for CLIP.
- `keywords` (optional, default empty) — seeds the accumulated keyword text, e.g. with a base style prompt, before any chained LoRA adds its own.

## Output

- `model_clip_text` — struct bundling `model`, `clip`, and `keywords`. This is the node's only output — use **Phoenix Unpack Model/Clip/Text** if you need `model`/`clip`/`keywords` back out separately.
