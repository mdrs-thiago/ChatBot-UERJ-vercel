import re
from typing import List


def split_juridical_chunks(text: str, max_len: int = 600) -> List[str]:
    chunks = []
    hierarchy = {
        "chapter": "",
        "article": "",
        "paragraph": "",
        "inciso": "",
        "alinea": "",
    }
    buffer = []

    patterns = {
        "chapter": r"^(CAPÍTULO|TÍTULO)\s+[A-ZÀ-Ÿ0-9\s]+(?:\n[A-ZÀ-Ÿ0-9\s]+)?",
        "article": r"^\s*Art\.?\s*\d+[ºo]?",
        "paragraph": r"^§ ?\d+[ºo]?",
        "inciso": r"^[IVXLCDM]+ –",
        "alinea": r"^[a-z]\)",
    }

    def flush_buffer():
        nonlocal buffer
        if buffer:
            chunks.append("\n".join(buffer).strip())
            buffer = []

    def current_hierarchy_text():
        return [v for v in hierarchy.values() if v]

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        for key, pat in patterns.items():
            if re.match(pat, line):
                hierarchy[key] = line
                keys = list(hierarchy.keys())
                idx = keys.index(key)
                for lower in keys[idx + 1 :]:
                    hierarchy[lower] = ""
                break

        hier_text = current_hierarchy_text()
        line_with_hierarchy = "\n".join(hier_text)

        prospective = "\n".join(buffer + [line_with_hierarchy])
        if len(prospective) > max_len:
            flush_buffer()
            buffer.extend(hier_text)
        if line not in buffer:
            buffer.append(line)

    flush_buffer()
    return chunks
