"""HTML ↔ Markdown conversion with Anki cloze and media preservation.

Media handling strategy
-----------------------
Anki stores images as bare filenames in <img> tags (e.g. <img src="paste-abc.png">)
and audio as [sound:file.mp3] literals.  Neither survives HTML↔Markdown conversion
cleanly, and we don't want the AI to corrupt or drop them.

Solution: extract both before conversion, replace with opaque internal placeholders
(MEDIA{i}AIDEM), convert only the text, then restore:

  HTML side  →  <img src="file.png">  and  [sound:file.mp3]
  MD side    →  [img:file.png]         and  [sound:file.mp3]

The [img:...] token is a readable, AI-visible format chosen deliberately so that
a future image-gen tool can produce new tokens of the same shape, upload the file
via AnkiConnect storeMediaFile, and inject [img:generated-abc.png] into the fields.
"""
import re
import markdown as md_lib
import markdownify


# ---------------------------------------------------------------------------
# Cloze placeholders  {{c1::text}}
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Media placeholders  <img ...>  and  [sound:...]
# ---------------------------------------------------------------------------

# Matches any <img ...> tag (self-closing or not, any attributes, case-insensitive)
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)

# Matches src="..." or src='...' inside an img tag
_IMG_SRC_RE = re.compile(r'\bsrc=["\']([^"\']*)["\']', re.IGNORECASE)

# Matches Anki's audio syntax — same form in HTML field values and in our markdown
_SOUND_RE = re.compile(r"\[sound:[^\]]+\]")

# Matches our readable image token in markdown
_IMG_TOKEN_RE = re.compile(r"\[img:[^\]]+\]")

# Internal placeholder used during conversion — all alphanum, ignored by both
# markdownify and python-markdown.  Pattern mirrors CLOZE{i}EZOLC.
_MEDIA_PLC_RE = re.compile(r"MEDIA(\d+)AIDEM")


def _encode_media_from_html(html: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace <img> tags and [sound:] tokens with indexed placeholders.

    Returns the modified string and a list of (kind, value) pairs where:
      kind == "img"   → value is the src filename
      kind == "sound" → value is the full [sound:...] token
    """
    media: list[tuple[str, str]] = []

    def replace_img(m: re.Match) -> str:
        src_match = _IMG_SRC_RE.search(m.group(0))
        if src_match is None:
            # Unparseable img tag — leave it alone rather than silently drop it
            return m.group(0)
        media.append(("img", src_match.group(1)))
        return f"MEDIA{len(media) - 1}AIDEM"

    def replace_sound(m: re.Match) -> str:
        media.append(("sound", m.group(0)))
        return f"MEDIA{len(media) - 1}AIDEM"

    html = _IMG_TAG_RE.sub(replace_img, html)
    html = _SOUND_RE.sub(replace_sound, html)
    return html, media


def _decode_media_to_markdown(text: str, media: list[tuple[str, str]]) -> str:
    """Restore placeholders as human-readable markdown tokens."""

    def restore(m: re.Match) -> str:
        i = int(m.group(1))
        if i >= len(media):
            return m.group(0)  # index out of range — leave placeholder intact
        kind, value = media[i]
        if kind == "img":
            return f"[img:{value}]"
        return value  # sound: already [sound:...] shaped

    return _MEDIA_PLC_RE.sub(restore, text)


def _encode_media_from_markdown(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace [img:] and [sound:] tokens with indexed placeholders."""
    media: list[tuple[str, str]] = []

    def replace_img_token(m: re.Match) -> str:
        # Strip the [img: prefix and trailing ]
        filename = m.group(0)[5:-1]
        media.append(("img", filename))
        return f"MEDIA{len(media) - 1}AIDEM"

    def replace_sound(m: re.Match) -> str:
        media.append(("sound", m.group(0)))
        return f"MEDIA{len(media) - 1}AIDEM"

    text = _IMG_TOKEN_RE.sub(replace_img_token, text)
    text = _SOUND_RE.sub(replace_sound, text)
    return text, media


def _decode_media_to_html(text: str, media: list[tuple[str, str]]) -> str:
    """Restore placeholders as HTML / Anki-native syntax."""

    def restore(m: re.Match) -> str:
        i = int(m.group(1))
        if i >= len(media):
            return m.group(0)
        kind, value = media[i]
        if kind == "img":
            return f'<img src="{value}">'
        return value  # sound: [sound:...] is valid as-is in Anki HTML fields

    return _MEDIA_PLC_RE.sub(restore, text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def html_to_markdown(html: str) -> str:
    text, clozes = _encode_clozes(html)
    text, media = _encode_media_from_html(text)
    text = markdownify.markdownify(text, heading_style="ATX", code_language="")
    text = _decode_media_to_markdown(text, media)
    text = _decode_clozes(text.strip(), clozes)
    return text


def markdown_to_html(text: str) -> str:
    text, clozes = _encode_clozes(text)
    text, media = _encode_media_from_markdown(text)
    text = md_lib.markdown(text, extensions=["fenced_code", "tables"])
    text = _decode_media_to_html(text, media)
    text = _decode_clozes(text, clozes)
    return text
