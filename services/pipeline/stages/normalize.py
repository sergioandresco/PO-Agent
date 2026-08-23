import re

from .types import Utterance

_UTTERANCE_PATTERN = re.compile(
    r"\[(?P<timestamp>\d{1,2}:\d{2}(?::\d{2})?)]\s*(?P<speaker>[^:\n]+):\s*"
    r"(?P<text>.*?)(?=\n\[\d{1,2}:\d{2}(?::\d{2})?]|\Z)",
    re.DOTALL,
)


def _parse_timestamp_ms(raw: str) -> int:
    parts = [int(part) for part in raw.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    hours, minutes, seconds = parts
    return ((hours * 60 + minutes) * 60 + seconds) * 1000


def normalize(raw_transcript: str) -> list[Utterance]:
    """Parses a `[HH:MM:SS] Speaker (Role): text` transcript into utterances,
    preserving the exact character span of each in the original text. Every
    SourceReference the pipeline ever produces traces back to these offsets."""
    utterances: list[Utterance] = []
    for index, match in enumerate(_UTTERANCE_PATTERN.finditer(raw_transcript)):
        utterances.append(
            Utterance(
                index=index,
                speaker=match.group("speaker").strip() or None,
                timestamp_ms=_parse_timestamp_ms(match.group("timestamp")),
                text=match.group("text").strip(),
                start_char_offset=match.start(),
                end_char_offset=match.end(),
            )
        )
    return utterances
