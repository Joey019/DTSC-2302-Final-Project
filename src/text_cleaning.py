import re

BOILERPLATE_PATTERNS = [
    r"(?i)arc provided by (the )?(publisher|author|netgalley).*",
    r"(?i)i received (an|a free) (advance )?(copy|review copy|arc).*",
    r"(?i)thank you to netgalley.*",
    r"<[^>]+>",
]

COMPILED_PATTERNS = [re.compile(p) for p in BOILERPLATE_PATTERNS]


def clean_review_text(text: str) -> str:
    cleaned = text
    for pattern in COMPILED_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()
