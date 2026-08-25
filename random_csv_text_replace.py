import random
import re

import server
from aiohttp import web

UNIQUE_KEYWORD = "_UNIQUE_"
NONE_KEYWORD = "_NONE_"
WEIGHT_PATTERN = re.compile(r"_(\d+(?:\.\d+)?)_")
NODE_TAG_PATTERN = re.compile(r"_NODE\(([^)]*)\)_")
NOTNODE_TAG_PATTERN = re.compile(r"_NOTNODE\(([^)]*)\)_")
TAG_PREFIX_PATTERN = re.compile(
    r"^\s*(?:(?:_\d+(?:\.\d+)?_|_NODE\([^)]*\)_|_NOTNODE\([^)]*\)_)\s*)*$"
)
CHANCE_OPEN = "_CHANCE("
CHANCE_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?|\.\d+")
CHANCE_PLACEHOLDER_PATTERN = re.compile("[ \\t]*\x00CH(\\d+)\x00")


def _scan_chance_block(text, start):
    """text[start:] must begin with _CHANCE(. Scans forward parsing
    whitespace-separated "WEIGHT "quoted text"" pairs (any number of
    them, no separator needed between pairs since each pair is
    self-delimiting) until the terminating )_. A doubled quote ("")
    inside a quoted option escapes a literal quote, matching
    _split_csv_row's own convention, so an option's text may contain
    commas, parens, anything except an unescaped quote. Returns
    (end_index, pairs) where end_index is the index just past the
    closing )_ and pairs is a list of (weight: float, text: str)
    tuples, in source order. Malformed input (a stray character where a
    number/quote was expected, or a block that's never closed) simply
    stops parsing at that point rather than raising, returning
    whatever end_index/pairs were reached so far."""
    n = len(text)
    i = start + len(CHANCE_OPEN)
    pairs = []
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i + 1 < n and text[i] == ')' and text[i + 1] == '_':
            return i + 2, pairs
        match = CHANCE_NUMBER_PATTERN.match(text, i)
        if not match:
            return i, pairs
        weight = float(match.group(0))
        i = match.end()
        while i < n and text[i].isspace():
            i += 1
        if i >= n or text[i] != '"':
            return i, pairs
        i += 1
        buf = []
        closed = False
        while i < n:
            c = text[i]
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    buf.append('"')
                    i += 2
                    continue
                i += 1
                closed = True
                break
            buf.append(c)
            i += 1
        if not closed:
            return i, pairs
        pairs.append((weight, "".join(buf)))
    return i, pairs


def _split_csv_row(line):
    """A CSV-row splitter like csv.reader, except a quote is recognized as
    opening a quoted field even when preceded by whitespace and/or weight
    (_2_) / _NODE(name)_ tags, e.g. _2_ _NODE(Real)_ "oily, dark". Python's
    csv module only treats a quote as special at the very start of a
    field, so a tag placed before a quoted field containing a comma would
    otherwise cause csv to split the field in the wrong place. A
    _CHANCE(...)_ block (see _scan_chance_block) is likewise copied
    through verbatim as a single unit regardless of where in the field
    it appears, so the commas inside its own quoted option texts don't
    get mistaken for field separators either."""
    fields = []
    buf = []
    in_quotes = False
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and line[i + 1] == '"':
                    buf.append('"')
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            buf.append(ch)
            i += 1
            continue
        if ch == ',':
            fields.append("".join(buf))
            buf = []
            i += 1
            continue
        if line.startswith(CHANCE_OPEN, i):
            end, _ = _scan_chance_block(line, i)
            buf.append(line[i:end])
            i = end
            continue
        if ch == '"' and TAG_PREFIX_PATTERN.match("".join(buf)):
            in_quotes = True
            i += 1
            continue
        buf.append(ch)
        i += 1
    fields.append("".join(buf))
    return fields


def _extract_chance_blocks(text):
    """Replaces every _CHANCE(...)_ block in text with a NUL-delimited
    placeholder (e.g. "\\x00CH0\\x00"), so the rest of _parse_candidate
    (weight/_NODE/_NOTNODE stripping, outer quote-stripping) never has
    to deal with the block's internal quotes/parens. Returns
    (text_with_placeholders, specs) where specs[i] is the parsed
    (weight, text) pairs list for placeholder CH<i>."""
    specs = []
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith(CHANCE_OPEN, i):
            end, pairs = _scan_chance_block(text, i)
            out.append(f"\x00CH{len(specs)}\x00")
            specs.append(pairs)
            i = end
            continue
        out.append(text[i])
        i += 1
    return "".join(out), specs


def _resolve_chance_placeholders(text, specs, rng):
    """Substitutes each CH<i> placeholder left by _extract_chance_blocks
    with one option picked (via the row's own seeded rng) from its
    pairs, weighted exactly like a normal candidate pick: if the pairs'
    weights sum to less than 1, an implicit ("", 1 - sum) option pads
    the remainder so nothing is picked that often; if the sum is >= 1,
    no padding happens and it's a plain weighted pick among the given
    options. Any spaces/tabs already in the source text right before the
    _CHANCE(...)_ block (typically just there for readability, e.g. "...
    _CHANCE(...)_") are consumed along with the placeholder itself: a
    picked non-empty option gets exactly one space inserted before it
    instead (any leading whitespace already in the option text is
    dropped first, so authors don't have to worry about doubling it up),
    while a picked empty option inserts nothing at all, not even a
    space — so the surrounding text's own formatting never leaks an
    extra/missing space into the result either way."""
    def repl(match):
        pairs = specs[int(match.group(1))]
        options = list(pairs)
        total = sum(weight for weight, _ in options)
        if total < 1:
            options.append((1 - total, ""))
        picked = rng.choices(options, weights=[weight for weight, _ in options], k=1)[0][1]
        picked = picked.lstrip()
        return f" {picked}" if picked else ""

    return CHANCE_PLACEHOLDER_PATTERN.sub(repl, text)


def _parse_candidate(candidate):
    """Splits a candidate like '_NODE(A)_ _NOTNODE(B)_ _2_ "blue, thick"
    _CHANCE(.2 "with scars" .3 " with fish scales")_' into its display
    text "blue, thick" (its _CHANCE(...)_ block(s) left as unresolved
    NUL-delimited placeholders — see _extract_chance_blocks/
    _resolve_chance_placeholders — since which option they resolve to
    depends on whether this very candidate ends up picked), its weight
    2.0 (default 1.0 without a _NUMBER_ token), the node names tagged on
    it via _NODE(...)_, e.g. ["A"], and the node names tagged on it via
    _NOTNODE(...)_, e.g. ["B"] (a candidate can carry any number of
    either tag, or none). _CHANCE(...)_ blocks are extracted first, so
    the quotes/commas/whitespace inside them never confuse the
    _NODE/_NOTNODE/weight parsing or the outer quote-stripping below
    (which is mostly a defensive fallback, since quotes around the
    display text are already stripped by _split_csv_row)."""
    text, chance_specs = _extract_chance_blocks(candidate)
    node_names = [name.strip() for name in NODE_TAG_PATTERN.findall(text) if name.strip()]
    notnode_names = [name.strip() for name in NOTNODE_TAG_PATTERN.findall(text) if name.strip()]
    text = NOTNODE_TAG_PATTERN.sub("", text)
    text = NODE_TAG_PATTERN.sub("", text)
    match = WEIGHT_PATTERN.search(text)
    if match:
        text = text[:match.start()] + text[match.end():]
        weight = float(match.group(1))
    else:
        weight = 1.0
    text = text.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    return text, weight, node_names, notnode_names, chance_specs


def _process_rows(terms, seed, unique):
    """Parses terms and picks one candidate per row exactly like
    PhoenixRandomCSVTextReplace.replace() does, for rows that have
    candidates. Returns a list of per-row dicts: 'text' (the picked
    term), 'node_names' (the picked candidate's _NODE(...)_ tags),
    'notnode_names' (the picked candidate's _NOTNODE(...)_ tags),
    'pos_universe' (every node name tagged via _NODE(...)_ anywhere in
    that row) and 'neg_universe' (every node name tagged via
    _NOTNODE(...)_ anywhere in that row) — used both by replace() and by
    the /phoenix/random_csv_node_toggles endpoint that resolves node
    bypass state before a prompt is queued.

    A blank (or whitespace-only) line is skipped entirely rather than
    contributing an empty entry, so it does NOT reserve a slot for its
    own placeholder — every following line shifts up by one placeholder
    index instead. E.g. with 3 lines where line 2 is blank, line 3 is
    mapped to $2 (not $3), and $3 is left in the text untouched. Only a
    blank line at the very end is harmless, since it behaves the same as
    simply having one row fewer than there are placeholders."""
    rng = random.Random(seed)
    used = set()
    rows_out = []
    for row in (_split_csv_row(line) for line in terms.splitlines()):
        fields = [field.strip() for field in row if field.strip()]
        row_unique = unique or UNIQUE_KEYWORD in fields
        candidates = [f for f in fields if f != UNIQUE_KEYWORD]
        if not candidates:
            continue

        parsed = [_parse_candidate(c) for c in candidates]
        pos_universe = sorted({name for _, _, names, _, _ in parsed for name in names})
        neg_universe = sorted({name for _, _, _, names, _ in parsed for name in names})

        if candidates == [NONE_KEYWORD]:
            choice_text, choice_names, choice_notnode_names, choice_chance_specs = "", [], [], []
        else:
            pool = parsed
            if row_unique:
                remaining = [p for p in parsed if p[0] not in used]
                if remaining:
                    pool = remaining
            choice_text, _, choice_names, choice_notnode_names, choice_chance_specs = rng.choices(
                pool, weights=[w for _, w, _, _, _ in pool], k=1
            )[0]
            if row_unique:
                used.add(choice_text)

        choice_text = _resolve_chance_placeholders(choice_text, choice_chance_specs, rng)

        rows_out.append({
            "text": choice_text,
            "node_names": choice_names,
            "notnode_names": choice_notnode_names,
            "pos_universe": pos_universe,
            "neg_universe": neg_universe,
        })
    return rows_out


def _resolve_node_toggles(terms, seed, unique):
    """Resolves which _NODE(name)_/_NOTNODE(name)_-tagged nodes should be
    active vs. bypassed for a run.

    _NODE(name)_ (positive tag): the row's picked candidate carrying it
    makes name active; the row merely mentioning name elsewhere (via
    _NODE) bypasses it by default.

    _NOTNODE(name)_ (negative tag, inverse of the above): the row's
    picked candidate carrying it makes name bypassed; the row merely
    mentioning name elsewhere (via _NOTNODE) leaves it active by
    default.

    If the picked candidate itself carries an explicit tag for name
    (positive or negative), that decides it directly. Otherwise the
    default above applies, based on how name was tagged elsewhere in the
    row. Rows are applied in order, so a name mentioned in more than one
    row takes its state from the last row that mentions it."""
    state = {}
    for row in _process_rows(terms, seed, unique):
        chosen_pos = set(row["node_names"])
        chosen_neg = set(row["notnode_names"])
        for name in row["pos_universe"]:
            if name in chosen_pos:
                state[name] = True
            elif name in chosen_neg:
                state[name] = False
            else:
                state[name] = False
        for name in row["neg_universe"]:
            if name in chosen_pos:
                state[name] = True
            elif name in chosen_neg:
                state[name] = False
            elif name not in row["pos_universe"]:
                state[name] = True
    return state


@server.PromptServer.instance.routes.post("/phoenix/random_csv_node_toggles")
async def _random_csv_node_toggles_route(request):
    data = await request.json()
    state = _resolve_node_toggles(
        data.get("terms", ""),
        int(data.get("seed", 0)),
        bool(data.get("unique", False)),
    )
    return web.json_response(state)


class PhoenixRandomCSVTextReplace:
    """Replaces sequential placeholders (search_string + index) in a text
    with a random term picked from a per-placeholder candidate list. The
    candidate lists are given as CSV: each row is one placeholder's
    candidates, row order maps to start_index, start_index+1, ... — so any
    number of placeholders is supported, and quoted fields let a candidate
    contain a comma. start_index also lets you chain several of these
    nodes to cover a larger range. Same seed + same terms always picks the
    same term. A placeholder past the last CSV row is left unchanged.
    Note that a blank line is NOT a no-op placeholder-preserving row: it
    is skipped entirely, so every row after it shifts up by one
    placeholder index (e.g. a blank line 2 makes line 3 map to $2, not
    $3) — only a blank line at the very end is harmless.

    Rows are independent by default, so the same term can be picked for
    more than one placeholder. Set 'unique' to make every row avoid terms
    already picked by another unique row this run, or mark only specific
    rows by adding the literal field _UNIQUE_ to that row's CSV — it's
    stripped out before picking, it isn't itself a candidate. If a unique
    row's candidates are all already taken, it falls back to picking from
    the full list rather than leaving the placeholder unresolved.

    A row whose only field is _NONE_ removes its placeholder from the
    output entirely instead of substituting a term — e.g. row 5
    containing just _NONE_ deletes $5 rather than leaving "$5" or
    "_NONE_" behind.

    A candidate may contain a _NUMBER_ token (e.g. "_2_ green") to weight
    how often it's picked relative to the row's other candidates (default
    weight 1); the token is stripped from the term before use. E.g. for
    "red, _2_ green, _0.1_ blue", green comes up twice as often as red,
    and blue only a tenth as often as red.

    A candidate may also carry any number of _NODE(nodename)_ tags (e.g.
    "_NODE(A)_ _NODE(B)_ red"), where nodename is the title of another
    node in the graph. Before a prompt is queued, a companion JS
    extension resolves, for every row, which node names are tagged on
    the candidate that would be picked with the current seed: those are
    set active, and every other node name tagged anywhere else in that
    same row is set to bypass. A name mentioned in more than one row
    takes its state from the last such row. This only takes effect at
    queue time (via a *_node_toggle.js companion script hitting the
    /phoenix/random_csv_node_toggles endpoint), not during this node's
    own execution, since node bypass state is fixed before a prompt
    starts running.

    _NOTNODE(nodename)_ works exactly like _NODE(nodename)_, but
    inverted: the candidate carrying it bypasses nodename when picked,
    while every other candidate in that row leaves nodename active
    unless it carries its own _NOTNODE(nodename)_ tag. _NODE and
    _NOTNODE can be mixed for the same name in the same row; a candidate
    with an explicit tag (either kind) always wins for that name.

    A candidate may also carry any number of _CHANCE(...)_ blocks — a
    nested weighted pick, resolved only if that candidate itself gets
    picked, and substituted in place. Each block holds any number of
    WEIGHT "text" pairs (no separator needed between pairs, e.g.
    _CHANCE(.2 "with scars" .3 "with fish scales")_): if the weights sum
    to less than 1 the remainder silently resolves to nothing being
    inserted (so with .2 + .3 here, 50% of the time neither option is
    inserted); if the sum is 1 or more, it's a plain weighted pick with
    no such padding. A picked option gets exactly one space inserted
    before it — any whitespace already written before the block in the
    source text (e.g. for readability) is absorbed into that, so it
    never doubles up or leaves a stray space when the pick is empty. An
    option's text may contain commas (quote it like any CSV field with a
    comma), but not an unescaped double quote (use "" to embed a literal
    one) or unmatched parens."""

    DESCRIPTION = (
        "Replaces sequential placeholders (search_string + index, e.g. "
        "$1, $2, ...) in a text with a random term picked from a "
        "per-placeholder candidate list. terms is CSV: each row is one "
        "placeholder's comma-separated candidates (quote a field to "
        "include a literal comma), row order maps to start_index, "
        "start_index+1, ... — any number of rows/placeholders is "
        "supported. start_index also lets you chain several of these "
        "nodes to cover a larger range, e.g. one node covering $1-$5, a "
        "second with start_index=6 covering $6-$10. Same seed + same "
        "terms always picks the same term. A placeholder past the last "
        "CSV row is left unchanged; a blank line, though, is skipped "
        "entirely rather than preserving its own placeholder, so every "
        "row after it shifts up by one index — only a trailing blank "
        "line is harmless. Rows are independent by "
        "default (the same term can come up more than once); enable "
        "'unique' to forbid that across all rows, or add the literal "
        "field _UNIQUE_ to only specific CSV rows to opt just those in — "
        "the keyword itself is removed before picking, not a candidate. "
        "If a unique row's candidates are all already used, it falls "
        "back to the full list instead of failing. A row whose only "
        "field is _NONE_ removes its placeholder from the output "
        "entirely instead of substituting a term. A candidate may "
        "contain a _NUMBER_ token (e.g. \"_2_ green\") to weight how "
        "often it's picked relative to the row's other candidates "
        "(default weight 1); the token is stripped from the term before "
        "use. A candidate may also carry any number of _NODE(nodename)_ "
        "tags naming another node in the graph by title; at queue time "
        "(not during this node's own execution) a companion JS extension "
        "activates the node names tagged on each row's picked candidate "
        "and bypasses every other node name mentioned elsewhere in that "
        "row, with the last row mentioning a given name winning. "
        "_NOTNODE(nodename)_ is the inverse: the candidate carrying it "
        "bypasses nodename when picked, other candidates in the row "
        "leave it active unless they carry their own _NOTNODE tag for "
        "it. A candidate may also carry _CHANCE(...)_ blocks: a nested "
        "weighted pick of WEIGHT \"text\" pairs, resolved and inserted "
        "in place only if that candidate is picked, e.g. _CHANCE(.2 "
        "\"with scars\" .3 \"with fish scales\")_ — weights summing to "
        "under 1 silently leave the remainder blank, 1 or more is a "
        "plain weighted pick. Shows the result in a read-only preview widget on the node itself. "
        "Also outputs replaced_text: just the picked term for each "
        "processed row, one per line in row order (rows with a "
        "missing/empty CSV line are skipped, _NONE_ rows contribute an "
        "empty line)."
    )
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "A $1 riding a $2 through $3.",
                    "tooltip": "Text containing the placeholders to be replaced.",
                }),
                "search_string": ("STRING", {
                    "multiline": False, "default": "$",
                    "tooltip": 'Prefix before the placeholder index, e.g. "$" makes placeholders $1, $2, ...',
                }),
                "start_index": ("INT", {
                    "default": 1, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "First placeholder index. Chain multiple nodes by offsetting this, e.g. 1 then 6 for $1-$5 and $6-$10.",
                }),
                "terms": ("STRING", {
                    "multiline": True,
                    "default": 'goose,wizard,astronaut\nmoped,unicycle,tank\n"a forest, at night",downtown,the moon',
                    "tooltip": (
                        "CSV: one row per placeholder, row order = start_index, start_index+1, ... "
                        "Any number of rows/columns. Quote a field to include a literal comma, e.g. \"a, b\",c. "
                        "A blank line is skipped entirely, not treated as an empty row, so every row below it "
                        "shifts up by one placeholder index instead of leaving its own placeholder unchanged — "
                        "avoid blank lines except at the very end. "
                        "Add the field _UNIQUE_ to a row to make just that row avoid terms already picked by "
                        "another unique row this run (it's removed before picking, not a candidate itself). "
                        "A row containing only _NONE_ removes its placeholder from the output instead of "
                        "substituting a term. Add a _NUMBER_ token to a candidate, e.g. \"_2_ green\", to "
                        "weight how often it's picked relative to the row's other candidates (default 1); "
                        "the token is stripped from the term before use. Add any number of _NODE(nodename)_ "
                        "tags to a candidate to name other nodes (by title) to activate when it's picked; "
                        "at queue time every other node name mentioned elsewhere in that row is bypassed "
                        "instead (last row mentioning a name wins). _NOTNODE(nodename)_ is the inverse: "
                        "the candidate carrying it bypasses nodename when picked, other candidates in the "
                        "row leave it active unless they carry their own _NOTNODE tag for it. Add any "
                        "number of _CHANCE(...)_ blocks to a candidate for a nested weighted pick, resolved "
                        "and inserted in place only if that candidate is picked, e.g. _CHANCE(.2 \"with "
                        "scars\" .3 \"with fish scales\")_ — any number of WEIGHT \"text\" pairs, no "
                        "separator needed between them; weights summing to under 1 silently leave the "
                        "remainder blank that often, 1 or more is a plain weighted pick with no padding. "
                        "A picked option gets exactly one space inserted before it, absorbing any "
                        "whitespace already written before the block for readability."
                    ),
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                    "tooltip": "Controls which term is picked. Same seed + same terms always gives the same result.",
                }),
                "unique": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "If enabled, every row avoids terms already picked by another row this run, so no term "
                        "is used twice. Off by default (rows are independent, terms can repeat). To make only "
                        "some rows unique instead of all, leave this off and add _UNIQUE_ to those rows' terms."
                    ),
                }),
            },
            "optional": {
                "preview": ("STRING", {
                    "multiline": True, "default": "",
                    "tooltip": "Read-only preview of the last result. Not an input; updates after each run.",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "replaced_text")
    FUNCTION = "replace"
    CATEGORY = "phoenix/text"

    def replace(self, text, search_string, start_index, terms, seed, unique=False, preview=""):
        result = text
        replaced = []
        for offset, row in enumerate(_process_rows(terms, seed, unique)):
            replaced.append(row["text"])
            placeholder = f"{search_string}{start_index + offset}"
            result = result.replace(placeholder, row["text"])
        replaced_text = "\n".join(replaced)
        return {"ui": {"text": [result]}, "result": (result, replaced_text)}


NODE_CLASS_MAPPINGS = {
    "PhoenixRandomCSVTextReplace": PhoenixRandomCSVTextReplace,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhoenixRandomCSVTextReplace": "Phoenix Random CSV Text Replace",
}
