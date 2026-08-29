# ComfyUI-phoenix-text-nodes

Custom node pack for ComfyUI.

## Nodes

- **PhoenixRandomCSVTextReplace** — replaces consecutive placeholders ($1, $2, ...) in a text with a randomly chosen term from a CSV candidate list (one line per placeholder). Ported from [comfyui-text-placeholder-randomizer](https://github.com/Arkarit/comfyui-text-placeholder-randomizer), whose `RandomCSVTextReplace` node continues to exist independently.
  - A line starting with `#` (leading whitespace ignored) is a comment — ignored entirely, exactly like a blank line (see below), not treated as an empty row.
  - By default, lines are independent — the same term can be drawn more than once.
  - `unique` (bool): when enabled, prevents a term from being drawn for more than one placeholder in a given run (across lines).
  - Fine-grained control per line: add the field `_UNIQUE_` to a CSV line to make only that line (or lines) mutually unique — independent of the `unique` bool. The keyword is removed from the candidate list before selection, so it can never be picked as a value itself. It only has an effect between multiple lines marked this way (with only one marked line, there is nothing for it to be distinct from). If all candidates for a unique line are already taken, it still draws from the full list (repetition instead of an unresolved placeholder).
  - If a line contains only the field `_NONE_` (e.g. line 5 = `_NONE_`), the corresponding placeholder (`$5`) is removed from the output entirely instead of being replaced by a term.
  - A candidate can carry a weight by including a number between two underscores, e.g. `red, _2_ green, _0.1_ blue` — `green` is picked twice as often as `red`, `blue` only a tenth as often as `red` (default weight is 1). The `_NUMBER_` token is stripped from the term before use.
  - `replaced_text` (output) — just the picked terms, one per line in row order, for rows that were actually processed (a row with a missing/empty CSV line is skipped; a `_NONE_` row contributes an empty line).
  - A candidate can carry any number of `_NODE(nodename)_` tags, where `nodename` is the *title* of another node in the graph, e.g. `_NODE(A)_ _NODE(B)_ red`. Before a prompt is queued, the node names tagged on each row's picked candidate are activated, and every other node name mentioned anywhere else in that row is set to bypass (last row mentioning a name wins). This only takes effect at queue time via the companion `js/random_csv_text_replace_node_toggle.js` extension (which resolves the pick through the `/phoenix/random_csv_node_toggles` endpoint, reusing this node's own selection logic) — not during this node's own execution, since a prompt's node bypass state is already fixed by the time any node runs. The `seed`/`unique`/`terms` widgets can themselves be link-driven (e.g. a global seed distributed via KJNodes' `SetNode`/`GetNode`) — the extension walks through such virtual pass-through nodes to find a concrete value, so this still works as long as the chain bottoms out at a plain widget or a primitive node with one clear value widget.
  - `_NOTNODE(nodename)_` tags work like `_NODE(nodename)_` but inverted: the candidate carrying it *bypasses* `nodename` when picked, while every other candidate in that row leaves `nodename` active — unless it carries its own `_NOTNODE(nodename)_` tag for the same name. `_NODE` and `_NOTNODE` tags for the same name can be mixed within one row; whichever tag (either kind) the picked candidate carries for that name decides it directly.
  - A candidate can carry any number of `_CHANCE(...)_` blocks: a nested weighted pick, resolved (and inserted right where the block sits) only if that candidate itself is picked. A block holds any number of `WEIGHT text` pairs with no separator needed between them, e.g. `smiling _CHANCE(0.2 happy 0.3 sad)_` — if the weights sum to less than 1 the remainder silently resolves to nothing (so here, 50% of the time neither option is inserted); if the sum is 1 or more, it's a plain weighted pick with no such padding. A picked option gets exactly one space inserted before it, absorbing any whitespace already written before the block in the source (so writing it with a leading space for readability, like the example above, doesn't create a double space, and an empty pick doesn't leave a stray trailing one). A single-word option needs no quotes; quote it (like any CSV field with a comma) only if it needs whitespace, a comma, or a paren in its text, e.g. `_CHANCE(.2 "with scars" .3 "big, scary")_` — an unescaped double quote isn't allowed inside a quoted option (double it, `""`, to embed a literal one).
- **PhoenixSaveText** — saves standalone text using the same `filename_prefix` scheme (including `%date%` placeholders, subfolders) and auto-counter logic as `Save Image`. The counter is based only on its own `.txt` history — for text that must guaranteedly get the same number as an associated image, use **PhoenixSaveImageAndText** instead (see below).
- **PhoenixSaveImageAndText** — saves images together with up to two optional accompanying texts (e.g. captions) using the same scheme as `Save Image`. All files share a single counter computed within this one function call, e.g. `AAA/myImage_00023_.png` + `AAA/myImage_00023_.txt` — guaranteeing they stay in sync regardless of how the rest of the graph is wired. (Two separate Save Image / Save Text nodes both fed directly from the same image source have *no* enforced execution order relative to each other — depending on which runs first, the number can shift by one. Hence this combined node when image and text belong together.)
  - `text` is optional — left unconnected, only the image is saved, no `.txt`.
  - `text2` (optional) — a second, independent text (e.g. an alternate caption variant); left unconnected, it isn't saved. The filename uses `text2_postfix` (default `"2"`) as a suffix before the extension, e.g. `AAA/myImage_00023_2.txt`.
  - `path` (optional) completely overrides `filename_prefix`/counter: a full path without extension, e.g. from another instance of this node. The image is saved as `<path>.png`, `text` (if given) as `<path>.txt`, `text2` (if given) as `<path><text2_postfix>.txt`. This makes it usable outside the ComfyUI output folder too (e.g. writing directly into a training dataset).
  - The `path` output produces exactly the format expected by another instance of this node's `path` input — for chaining multiple Save nodes onto the same path.
  - `seed` (optional, int) — if connected, an extra empty marker file is written alongside the image: same base name plus `seed_<value>`, no extension (e.g. `dream_00470_.png` → `dream_00470_seed_1234567`).
- **PhoenixAppendText** — appends a fixed text field to an incoming string and outputs the result.
- **PhoenixPrependText** — prepends a fixed text field to an incoming string and outputs the result.
- **PhoenixFlexConcat** — inserts any number of connected values (of any type, converted to text) into a text template using `$1`, `$2`, ... placeholders, in socket order.
  - `count`: how many `input_N` sockets the node shows (up to 100) — the node's UI adds/removes sockets live as you change it.
  - If `text` is left completely empty, the connected values are joined with newlines instead of being substituted into a template.
  - `search_string`: prefix before the placeholder index (default `$`), same convention as `PhoenixRandomCSVTextReplace`.
- **PhoenixCarriageReturn** — outputs a string of `number` newline characters, e.g. to pad text before concatenation.
- **PhoenixFilterComments** — removes comment lines (lines starting with `#`, leading whitespace ignored) from an incoming string entirely, so they never reach whatever comes next — e.g. chain it in front of a normal `CLIP Text Encode` to let a prompt carry notes or temporarily-disabled lines without them being encoded. Every other line passes through unchanged.
- **PhoenixLoadText** — loads a `.txt` file via a path with wildcards (`*`, `?`, `[seq]`, `**` for recursive), e.g. `input/random/random*.txt`. Relative paths are resolved against the ComfyUI root; matches are sorted alphabetically.
  - `index`: `-1` = pick a random match (via `seed`), `0` = take the first match, `>0` = the match at this position (`1` = second match, ...).
  - `seed` + `control_after_generate`: same as KSampler — only used when `index = -1`.
  - `alternative_text` (optional, default empty) — output used for `text` when no file could be loaded, instead of an empty string.
  - `loaded` (bool output) — `true` if the text came from a file, `false` if `alternative_text` was used instead.
  - `preview`: read-only widget showing the loaded text, or "No Text found" plus a reason when there's no match (no path, no match, index out of range, file not readable), noting that the alternative text was used.

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
