# Phoenix Random CSV Text Replace

Replaces sequential placeholders (`search_string` + index, e.g. `$1`, `$2`, ...) in `text` with a random term picked from a per-placeholder candidate list in `terms`.

`terms` is CSV: each row is one placeholder's comma-separated candidates (quote a field to include a literal comma). Row order maps to `start_index`, `start_index+1`, ... — any number of rows/placeholders is supported. Chain several nodes to cover a larger range by offsetting `start_index`, e.g. one node covering `$1`-`$5`, a second with `start_index=6` covering `$6`-`$10`.

Same `seed` + same `terms` always picks the same term. A placeholder past the last CSV row is left unchanged. A blank line, or a comment line starting with `#` (leading whitespace ignored), is skipped entirely rather than preserving its own placeholder, so every row after it shifts up by one index — only a trailing blank/comment line is harmless.

## Continuation lines

A long row with many candidates gets unreadable on one line, so a row may be split over several source lines: **if a line's first non-blank character is a comma, it is appended to the last preceding line that had content** instead of starting a row of its own.

```
ocean, cat, dog, door, hallway
# animals above, places below

, forest, mountain, desert
, castle, palace, garden
```

is one single row, identical to `ocean, cat, dog, door, hallway, forest, mountain, desert, castle, palace, garden`. Blank lines and `#` comment lines in between are ignored as usual and do **not** break the continuation, so you can group and annotate a long list freely.

This deliberately departs from plain CSV. Two consequences worth knowing:

- Only a *leading* comma continues a row. A trailing comma does **not** — that would make a forgotten comma at the end of a line silently swallow the next row.
- A line that previously formed its own row purely because it started with a comma (leaving an empty first field, which was dropped) now merges into the row above it instead.

A continuation line with no content line before it has nothing to attach to and stays a row of its own; its leading comma just produces an empty first field, which is dropped like any other empty field.

## Candidate tags at a glance

| Tag | Effect |
| --- | --- |
| `#...` (whole line) | Comment line — ignored entirely, just like a blank line. |
| `,...` (line start) | Continuation — the line is appended to the previous content line. |
| `_UNIQUE_` | Marks this row as mutually unique with other `_UNIQUE_` rows this run. |
| `_NONE_` | Row's only field → removes its placeholder from the output entirely. |
| `_NUMBER_` (e.g. `_2_`) | Weights how often the candidate is picked (default 1). |
| `_NODE(name)_` | Activates node `name` when this candidate is picked, bypasses it otherwise. |
| `_NOTNODE(name)_` | Inverse of `_NODE`: bypasses `name` when picked, active otherwise. |
| `_CHANCE(...)_` | Nested weighted pick, resolved only if this candidate is picked. |
| `_DEFINE("name")_` | Defines `name` when this candidate is picked. |
| `_IF("name")_` | Gates this candidate on `name` being defined (exclusive, see below). |

## Conditions: `_DEFINE` and `_IF`

A candidate can define a variable when it is picked, and candidates elsewhere can be gated on it.

```
Row in an early node:   Wald, See _DEFINE("See")_
Row in a later node:    Ein Spaziergang, _IF("See")_ Eine Bootfahrt
```

If `See` is picked in the first node, the second row can only pick `Eine Bootfahrt`; otherwise only `Ein Spaziergang`.

### Wiring it up

Variables travel along the `defines` input/output sockets, not by magic:

- `defines` (input, optional) — the variable names arriving from an earlier node. Unconnected means no variable is defined.
- `defines` (output) — the names in effect after this node's last row.
- `pass_through_defines` (widget, default **on**) — whether the incoming names are forwarded to the output alongside this node's own. Turn it off to start a fresh scope.

With forwarding off, incoming names still participate in this node's conditions.
Only names defined by its picked candidates leave the output, including names
that were already present on the input and are defined again here.

Because it is a real link, ComfyUI orders the two nodes correctly on its own, and caching stays correct: a node's cache key already includes all of its ancestors, so changing the defining node re-runs the gated one.

Within a single node no link is needed — rows are processed top to bottom, so a later row already sees what an earlier row defined.

### Gating is exclusive

In a row where **at least one** candidate's condition is satisfied, only the satisfied candidates can be picked. If none is satisfied, only the candidates carrying no `_IF(...)_` at all can be.

| `Ein Spaziergang, _IF("See")_ Eine Bootfahrt` | eligible |
| --- | --- |
| `See` defined | `Eine Bootfahrt` only |
| `See` not defined | `Ein Spaziergang` only |

If that leaves nothing to pick, the row behaves like `_NONE_`: its placeholder is removed, but the row keeps its index, so the numbering of all following rows stays put.

### AND / OR

Names inside one tag are ANDed, separate tags are ORed:

```
_IF("See" "Meer")_ needs both
_IF("See")_ _IF("Meer")_ needs either
```

`_DEFINE("a" "b")_` likewise defines several names at once. Names may be quoted or bare words (`_IF(See)_`), the same as option texts in `_CHANCE(...)_`.

### With `_NODE(...)_`

Combining the two works: the pre-queue pass that resolves `_NODE(...)_` walks the same `defines` chain, so the LoRA a gated candidate activates matches the text that candidate produces.

A bypassed Random CSV node in that chain forwards its incoming definitions
unchanged. Its own candidate tags and `pass_through_defines` setting are ignored.

## Uniqueness

Rows are independent by default (the same term can come up more than once). Enable `unique` to forbid that across all rows, or add the literal field `_UNIQUE_` to only specific CSV rows to opt just those in — the keyword is removed before picking, not a candidate itself. If a unique row's candidates are all already used, it falls back to the full list instead of failing.

## `_NONE_`

A row whose only field is `_NONE_` removes its placeholder from the output entirely instead of substituting a term.

## Weighting

A candidate may contain a `_NUMBER_` token (e.g. `"_2_ green"`) to weight how often it's picked relative to the row's other candidates (default weight 1); the token is stripped from the term before use.

Example: `red, _2_ green, _0.1_ blue` — `green` comes up twice as often as `red`, `blue` only a tenth as often as `red`.

## `_NODE(nodename)_` / `_NOTNODE(nodename)_`

A candidate may carry any number of `_NODE(nodename)_` tags naming another node in the graph by title. At queue time (not during this node's own execution) a companion JS extension activates the node names tagged on each row's picked candidate, and bypasses every other node name mentioned elsewhere in that row — the last row mentioning a given name wins.

`_NOTNODE(nodename)_` is the inverse: the candidate carrying it bypasses `nodename` when picked, while other candidates in the row leave it active unless they carry their own `_NOTNODE` tag for it.

`_NODE` and `_NOTNODE` for the same name can be mixed within one row; whichever tag the picked candidate itself carries decides it directly.

## `_CHANCE(...)_`

A candidate may also carry any number of `_CHANCE(...)_` blocks: a nested weighted pick of `WEIGHT "text"` pairs, resolved and inserted in place only if that candidate is picked.

```
"blue, thick" _CHANCE(.2 "with scars" .3 "with fish scales")_
```

- Weights summing to under 1 silently leave the remainder blank that often — here, 50% of the time neither option is inserted.
- 1 or more is a plain weighted pick with no padding.
- A picked option gets exactly one space inserted before it, absorbing any whitespace already written before the block for readability.
- A single-word option needs no quotes at all, e.g. `_CHANCE(0.2 happy 0.3 sad)_`. Quote it only if the text needs whitespace, a comma, or a paren, e.g. `_CHANCE(0.2 "with scars" 0.3 "big, scary")_` — an unescaped double quote isn't allowed inside a quoted option (double it, `""`, to embed a literal one).

## Outputs

- `text` — the input text with placeholders replaced.
- `replaced_text` — just the picked term for each processed row, one per line in row order (rows with a missing/empty CSV line are skipped, `_NONE_` rows contribute an empty line).
- A read-only `preview` widget on the node itself shows the last result.
