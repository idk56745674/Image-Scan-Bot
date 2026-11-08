import re

MAX_TAG_WORDS = 6


def normalize_phrase(text: str) -> str:
    text = text.lower().replace("'", "")
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def parse_tags(text: str) -> list[str]:
    seen: dict[str, None] = {}
    for part in text.split(","):
        tag = normalize_phrase(part)
        if tag and len(tag.split()) <= MAX_TAG_WORDS:
            seen.setdefault(tag, None)
    return list(seen)


def parse_query(text: str, vocab: set[str]) -> list[str]:
    if "," in text:
        seen: dict[str, None] = {}
        for part in text.split(","):
            term = normalize_phrase(part)
            if term:
                seen.setdefault(term, None)
        return list(seen)

    words = normalize_phrase(text).split()
    terms: dict[str, None] = {}
    i = 0
    while i < len(words):
        take = 1
        for n in range(min(MAX_TAG_WORDS, len(words) - i), 1, -1):
            if " ".join(words[i:i + n]) in vocab:
                take = n
                break
        terms.setdefault(" ".join(words[i:i + take]), None)
        i += take
    return list(terms)
