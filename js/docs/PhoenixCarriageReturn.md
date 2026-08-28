# Phoenix Carriage Return

Outputs a string made of `number` newline characters (`\n`), nothing else.

Useful for building a text template by hand where you need an actual multi-line gap — e.g. concatenating it between two other STRING inputs (via Flex Concat, Append Text, ...) instead of typing blank lines into a multiline widget.

## Input

- `number` — how many newline characters to output. `0` outputs an empty string.

## Output

- `text` — `number` newline characters, or an empty string if `number` is `0`.
