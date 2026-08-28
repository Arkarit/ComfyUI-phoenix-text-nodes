# Phoenix Flex Concat

Inserts any number of connected values into a text template, using the same placeholder mechanism as Phoenix Random CSV Text Replace (`search_string` + index, e.g. `$1`, `$2`, ...) — but always starting at 1, with no `start_index`.

## Sockets

`count` (1-100) sets how many input sockets the node shows — a frontend extension adds/removes them to match as you change the widget. Each socket (`input_1`, `input_2`, ...) is optional and typeless, so anything can be connected — a STRING, an INT (e.g. a seed), a FLOAT, whatever — and its value is converted to text before use. A socket left unconnected is simply skipped; its placeholder (if used in `text`) is left unchanged in the output.

## Template mode

With `text` non-empty, each connected `input_N` is substituted for its placeholder (`search_string` + `N`) anywhere it occurs in `text`:

```
text:      "A $1 riding a $2, seed=$3."
input_1:   "goose"
input_2:   "unicycle"
input_3:   1234567   (an INT, e.g. from a KSampler's seed)
→          "A goose riding a unicycle, seed=1234567."
```

Change `search_string` (default `$`) to use a different placeholder prefix, e.g. `@` for `@1`, `@2`, ...

## Empty-text fallback

If `text` is left completely empty, there's no template to substitute into — the connected values are instead joined with newlines, in socket order, skipping unconnected ones. This is the quick way to use the node as a plain multi-input concatenator without writing a template.

## Output

- `text` — the substituted template, or the newline-joined values if `text` was empty.
