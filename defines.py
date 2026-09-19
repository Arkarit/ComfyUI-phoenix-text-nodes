DEFINES_TYPE = "PHOENIX_DEFINES"


def normalize_defines(value):
    """Coerces whatever arrives on a `defines` input into a frozenset of
    non-empty names. An unconnected optional input arrives as None, which
    becomes the empty set, so a node with nothing wired in simply behaves
    as if no variable were defined."""
    if not value:
        return frozenset()
    if isinstance(value, str):
        return frozenset([value]) if value else frozenset()
    try:
        names = list(value)
    except TypeError:
        return frozenset()
    return frozenset(str(name) for name in names if str(name))
