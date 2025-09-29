import re
import unicodedata

pattern = re.compile(
    r"""
    resolu[cç][aã]o
    \s*
    (?:n[º°o\.]?\s*)?
    (\d{1,4})
    [\s./-]?
    (\d{1,4})
    """,
    re.IGNORECASE | re.VERBOSE,
)


def normalize_resolution(text: str) -> str | None:
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode()
    match = pattern.search(text)
    if match:
        num, ano = match.groups()
        num = num.strip().zfill(3)
        return f"{num}/{ano}"
    return None
