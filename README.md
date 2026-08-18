# ComfyUI-phoenix-text-nodes

Custom node pack for ComfyUI.

## Nodes

- **PhoenixRandomCSVTextReplace** — replaces consecutive placeholders ($1, $2, ...) in a text with a randomly chosen term from a CSV candidate list (one line per placeholder). Ported from [comfyui-text-placeholder-randomizer](https://github.com/Arkarit/comfyui-text-placeholder-randomizer), whose `RandomCSVTextReplace` node continues to exist independently.
  - By default, lines are independent — the same term can be drawn more than once.
  - `unique` (bool): when enabled, prevents a term from being drawn for more than one placeholder in a given run (across lines).
  - Fine-grained control per line: add the field `_UNIQUE_` to a CSV line to make only that line (or lines) mutually unique — independent of the `unique` bool. The keyword is removed from the candidate list before selection, so it can never be picked as a value itself. It only has an effect between multiple lines marked this way (with only one marked line, there is nothing for it to be distinct from). If all candidates for a unique line are already taken, it still draws from the full list (repetition instead of an unresolved placeholder).
  - If a line contains only the field `_NONE_` (e.g. line 5 = `_NONE_`), the corresponding placeholder (`$5`) is removed from the output entirely instead of being replaced by a term.
- **PhoenixSaveText** — saves standalone text using the same `filename_prefix` scheme (including `%date%` placeholders, subfolders) and auto-counter logic as `Save Image`. The counter is based only on its own `.txt` history — for text that must guaranteedly get the same number as an associated image, use **PhoenixSaveImageAndText** instead (see below).
- **PhoenixSaveImageAndText** — saves images together with up to two optional accompanying texts (e.g. captions) using the same scheme as `Save Image`. All files share a single counter computed within this one function call, e.g. `AAA/myImage_00023_.png` + `AAA/myImage_00023_.txt` — guaranteeing they stay in sync regardless of how the rest of the graph is wired. (Two separate Save Image / Save Text nodes both fed directly from the same image source have *no* enforced execution order relative to each other — depending on which runs first, the number can shift by one. Hence this combined node when image and text belong together.)
  - `text` is optional — left unconnected, only the image is saved, no `.txt`.
  - `text2` (optional) — a second, independent text (e.g. an alternate caption variant); left unconnected, it isn't saved. The filename uses `text2_postfix` (default `"2"`) as a suffix before the extension, e.g. `AAA/myImage_00023_2.txt`.
  - `path` (optional) completely overrides `filename_prefix`/counter: a full path without extension, e.g. from another instance of this node. The image is saved as `<path>.png`, `text` (if given) as `<path>.txt`, `text2` (if given) as `<path><text2_postfix>.txt`. This makes it usable outside the ComfyUI output folder too (e.g. writing directly into a training dataset).
  - The `path` output produces exactly the format expected by another instance of this node's `path` input — for chaining multiple Save nodes onto the same path.
- **PhoenixAppendText** — appends a fixed text field to an incoming string and outputs the result.
- **PhoenixLoadText** — loads a `.txt` file via a path with wildcards (`*`, `?`, `[seq]`, `**` for recursive), e.g. `input/random/random*.txt`. Relative paths are resolved against the ComfyUI root; matches are sorted alphabetically.
  - `index`: `-1` = pick a random match (via `seed`), `0` = take the first match, `>0` = the match at this position (`1` = second match, ...).
  - `seed` + `control_after_generate`: same as KSampler — only used when `index = -1`.
  - `preview`: read-only widget showing the loaded text, or "No Text found" plus a reason when there's no match (no path, no match, index out of range, file not readable). In that case, the `text` output is empty.

## Adding a new node

1. Create a new file (e.g. `my_node.py`) with the node class — at minimum `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, `CATEGORY` — plus its own `NODE_CLASS_MAPPINGS`/`NODE_DISPLAY_NAME_MAPPINGS` at the end of the file.
2. Import the file in `__init__.py` and merge its mappings into `NODE_CLASS_MAPPINGS`/`NODE_DISPLAY_NAME_MAPPINGS` (`{**a.NODE_CLASS_MAPPINGS, **b.NODE_CLASS_MAPPINGS}`).
3. Restart ComfyUI.

## Web extensions (JS)

`WEB_DIRECTORY = "js"` is active; `.js` files in the `js/` folder are loaded automatically (see `random_csv_text_replace_preview.js` for the preview widget of `PhoenixRandomCSVTextReplace`).

## Dependencies

Only add to `requirements.txt` when truly necessary — all node packs share Stability Matrix's ComfyUI venv, see `requirements.txt` for details on today's NumPy/numba update conflict.

## Publishing (optional)

`pyproject.toml` is prepared for the [Comfy Registry](https://registry.comfy.org) (`comfy node publish` via [comfy-cli](https://github.com/Comfy-Org/comfy-cli)). Adjust `PublisherId` and the repository URL before publishing.
