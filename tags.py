import re


def parse_tags(text: str) -> list[str]:
    text = text.lower().replace("'", "")
    text = re.sub(r"[^\w\s,]", " ", text)
    seen: dict[str, None] = {}
    for word in re.split(r"[\s,]+", text):
        if word:
            seen.setdefault(word, None)
    return list(seen)
