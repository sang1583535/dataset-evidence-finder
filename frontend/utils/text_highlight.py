import html
import re


def highlight_matched_alias(sentence: str, alias: str) -> str:
    if not alias or not alias.strip():
        return html.escape(sentence)

    pattern = re.compile(f"({re.escape(alias)})", re.IGNORECASE)
    parts = pattern.split(sentence)

    result = []
    for i, part in enumerate(parts):
        escaped = html.escape(part)
        if i % 2 == 1:
            result.append(f"<mark>{escaped}</mark>")
        else:
            result.append(escaped)

    return "".join(result)
