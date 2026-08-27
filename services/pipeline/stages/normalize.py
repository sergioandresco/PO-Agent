import re

from .types import Utterance

_UTTERANCE_START = r"(?:\[\d{1,2}:\d{2}(?::\d{2})?]\s*)?[^:\n]{1,60}(?<!\d):[ \t]"

_UTTERANCE_PATTERN = re.compile(
    rf"(?:\[(?P<timestamp>\d{{1,2}}:\d{{2}}(?::\d{{2}})?)]\s*)?"
    rf"(?P<speaker>[^:\n]{{1,60}}(?<!\d)):[ \t]*"
    rf"(?P<text>.*?)(?=\n{_UTTERANCE_START}|\Z)",
    re.DOTALL,
)

_START_MARKER = re.compile(r"\[\s*inicio\s+de\s+la\s+transcripci[oó]n\s*]", re.IGNORECASE)
_END_MARKER = re.compile(r"\[\s*fin\s+de\s+la\s+transcripci[oó]n\s*]", re.IGNORECASE)

_MEET_STYLE_HEADER = r"^[^\n:]{1,60}[ \t]+\d{1,2}:\d{2}(?::\d{2})?[ \t]*$"

_MEET_STYLE_PATTERN = re.compile(
    rf"^(?P<speaker>[^\n:]{{1,60}}?)[ \t]+(?P<timestamp>\d{{1,2}}:\d{{2}}(?::\d{{2}})?)[ \t]*\n"
    rf"(?P<text>.*?)(?=\n{_MEET_STYLE_HEADER}|\Z)",
    re.DOTALL | re.MULTILINE,
)


def _parse_timestamp_ms(raw: str) -> int:
    parts = [int(part) for part in raw.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    hours, minutes, seconds = parts
    return ((hours * 60 + minutes) * 60 + seconds) * 1000


def _extract(
    pattern: re.Pattern[str], raw_transcript: str, search_start: int, search_end: int
) -> list[Utterance]:
    utterances: list[Utterance] = []
    for index, match in enumerate(pattern.finditer(raw_transcript, search_start, search_end)):
        timestamp = match.group("timestamp")
        text = match.group("text").strip()
        if not text:
            continue
        utterances.append(
            Utterance(
                index=index,
                speaker=match.group("speaker").strip() or None,
                timestamp_ms=_parse_timestamp_ms(timestamp) if timestamp else None,
                text=text,
                start_char_offset=match.start(),
                end_char_offset=match.end(),
            )
        )
    return utterances


def normalize(raw_transcript: str) -> list[Utterance]:
    """Parses a transcript into utterances, preserving the exact character span
    of each in the original text. Every SourceReference the pipeline ever
    produces traces back to these offsets, never to LLM output.

    Tries, in order: `[HH:MM:SS] Speaker: text`, plain `Speaker: text`, and —
    only if neither finds anything — a `Speaker  H:MM` header line followed by
    the dialogue on the next line(s) (the shape Meet/Teams exports typically
    use; unverified against a real export, best-effort). This is a heuristic
    over a handful of known shapes, not a full transcript-format parser —
    unusual formats may still need preprocessing.
    """
    start_match = _START_MARKER.search(raw_transcript)
    end_match = _END_MARKER.search(raw_transcript)
    search_start = start_match.end() if start_match else 0
    search_end = end_match.start() if end_match else len(raw_transcript)

    utterances = _extract(_UTTERANCE_PATTERN, raw_transcript, search_start, search_end)
    if utterances:
        return utterances

    return _extract(_MEET_STYLE_PATTERN, raw_transcript, search_start, search_end)
