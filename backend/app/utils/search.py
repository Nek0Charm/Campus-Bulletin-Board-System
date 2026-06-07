import logging
import re

try:
    import jieba
except ImportError:  # pragma: no cover - exercised only in minimal local envs
    jieba = None

if jieba is not None:
    jieba.setLogLevel(logging.WARNING)

_WHITESPACE_RE = re.compile(r"\s+")
_ASCII_RE = re.compile(r"[a-zA-Z0-9_]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


def _fallback_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for match in re.finditer(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]+", text):
        value = match.group(0).lower()
        if _ASCII_RE.fullmatch(value):
            tokens.append(value)
            continue

        if _CJK_RE.fullmatch(value):
            tokens.append(value)
            if len(value) > 1:
                tokens.extend(value[i : i + 2] for i in range(len(value) - 1))
    return tokens


def tokenize_for_search(text: str) -> list[str]:
    """Tokenize Chinese and mixed-language text for PostgreSQL simple tsvector."""
    normalized = _WHITESPACE_RE.sub(" ", text.strip())
    if not normalized:
        return []

    raw_tokens = (
        jieba.cut_for_search(normalized)
        if jieba is not None
        else _fallback_tokens(normalized)
    )

    tokens: list[str] = []
    seen: set[str] = set()
    for token in raw_tokens:
        word = token.strip().lower()
        if not word or word in seen:
            continue
        seen.add(word)
        tokens.append(word)
    return tokens


def build_search_document(*parts: str | None) -> str:
    text = " ".join(part for part in parts if part)
    return " ".join(tokenize_for_search(text))
