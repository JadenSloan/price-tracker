"""Title cleanup utilities for building targeted sold-listing search queries."""

import re

_FILLER_WORDS = {
    "rare", "authentic", "bnwt", "bnib", "nwt", "nwot", "deadstock", "ds",
    "vtg", "vintage", "grail", "grailed", "og", "y2k", "hype", "fire",
    "steal", "brand", "new", "mint", "condition", "genuine", "real",
    "guaranteed", "sale", "cheap",
}
_SIZE_TOKENS = {
    "xs", "s", "m", "l", "xl", "xxl", "xxxl", "os", "one", "size",
    "small", "medium", "large",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def clean_title(
    title: str,
    *,
    max_tokens: int = 6,
    anchor_tokens: int = 2,
    extra_stopwords: set[str] | None = None,
) -> str:
    """Strip hype/filler and size tokens from a listing title, returning a
    short query string suitable for searching sold listings.

    When the cleaned title exceeds max_tokens, keeps a leading anchor (e.g.
    the brand/designer name) plus trailing tokens, since product-type words
    ("hoodie", "t shirt", "hat") tend to sit at the end of a title and matter
    more for search relevance than words in the middle.
    """
    if not title:
        return ""
    stop = _FILLER_WORDS | _SIZE_TOKENS | (extra_stopwords or set())
    tokens = _TOKEN_RE.findall(title.lower())
    kept = [t for t in tokens if t not in stop]

    if len(kept) <= max_tokens:
        return " ".join(kept)

    head = kept[:anchor_tokens]
    tail = kept[-(max_tokens - len(head)):]
    return " ".join(head + tail)
