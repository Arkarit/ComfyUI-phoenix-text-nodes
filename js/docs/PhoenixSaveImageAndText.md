# Phoenix Save Image + Text

Saves `images` to the ComfyUI output directory, together with up to two optional text files and an optional seed marker file — all computed from a single counter per call, so their numbers always stay in sync regardless of how the rest of the graph is wired.

## Filenames

Using the built-in Save Image counter scheme with `filename_prefix` (e.g. `myImage`):

| File | When |
| --- | --- |
| `myImage_00023_.png` | Always |
| `myImage_00023_.txt` | `text` connected |
| `myImage_00023_2.txt` | `text2` connected (suffix from `text2_postfix`, default `2`) |
| `myImage_00023_seed_1234567` | `seed` connected — empty marker file, no extension |

A batch of images gets `_0`, `_1`, ... appended to the base name (only relevant when `path` overrides the counter, see below — the normal counter-based scheme already gives each image in a batch its own number).

## `path`: exact save location

Connect `path` (e.g. from another instance of this node's own `path` output) to bypass `filename_prefix`/counter entirely and save at an exact location instead — a full path with no extension. The image is saved as `<path>.png`, text as `<path>.txt`, and so on. This also works for saving outside the ComfyUI output folder.

## `seed` marker file

If `seed` is connected (e.g. from a KSampler's seed), an empty file is written next to the image using the same base name plus `seed_<value>`, with no extension — e.g. `dream_00470_.png` → `dream_00470_seed_1234567`. Handy for spotting which seed produced a given image at a glance, without opening its embedded PNG metadata.

## Outputs

- `images` — passthrough of the input, so this node can sit inline.
- `text` — passthrough of `text`.
- `path` — the exact base path used for this call (no extension). Feed it into a second Save Image + Text node's `path` input to save an additional file under the identical name/counter.
