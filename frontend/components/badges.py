import html as _html


_BADGE_COLORS: dict[str, tuple[str, str]] = {
    "Hugging Face":             ("#FF9D00", "#fff"),
    "OpenML":                   ("#0066CC", "#fff"),
    "European Language Grid":   ("#1e7e34", "#fff"),
    "DataCite":                 ("#6f42c1", "#fff"),
    "abstract":                 ("#6c757d", "#fff"),
    "full_text_pdf":            ("#17a2b8", "#fff"),
}

_BADGE_LABELS: dict[str, str] = {
    "Hugging Face":             "HF",
    "European Language Grid":   "ELG",
    "full_text_pdf":            "full text",
}

_DEFAULT_COLOR = ("#343a40", "#fff")


def source_badge(source: str) -> str:
    bg, fg = _BADGE_COLORS.get(source, _DEFAULT_COLOR)
    label = _BADGE_LABELS.get(source, _html.escape(source))
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;'
        f'font-size:0.75em;font-weight:600;margin:1px 2px;'
        f'background:{bg};color:{fg}">{label}</span>'
    )


def render_badges(sources: list[str]) -> str:
    return "".join(source_badge(s) for s in sources)
