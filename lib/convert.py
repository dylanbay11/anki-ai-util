"""HTML ↔ Markdown conversion with Anki cloze preservation."""
import re
import markdown as md_lib
import markdownify


# Cloze syntax: {{c1::text}} — must survive both directions unchanged.
# Strategy: encode them to a placeholder before conversion, decode after.
_CLOZE_RE = re.compile(r"\{\{c\d+::.*?\}\}")


def _encode_clozes(text: str) -> tuple[str, list[str]]:
    clozes: list[str] = []

    def replacer(m: re.Match) -> str:
        clozes.append(m.group(0))
        return f"CLOZE{len(clozes) - 1}EZOLC"

    return _CLOZE_RE.sub(replacer, text), clozes


def _decode_clozes(text: str, clozes: list[str]) -> str:
    for i, cloze in enumerate(clozes):
        text = text.replace(f"CLOZE{i}EZOLC", cloze)
    return text


def html_to_markdown(html: str) -> str:
    encoded, clozes = _encode_clozes(html)
    result = markdownify.markdownify(encoded, heading_style="ATX", code_language="")
    return _decode_clozes(result.strip(), clozes)


def markdown_to_html(text: str) -> str:
    encoded, clozes = _encode_clozes(text)
    result = md_lib.markdown(encoded, extensions=["fenced_code", "tables"])
    return _decode_clozes(result, clozes)
