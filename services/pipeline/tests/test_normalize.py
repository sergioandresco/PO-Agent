from services.pipeline.stages.normalize import normalize

SAMPLE = (
    "[00:00:03] Ana (Product Manager): Buenas tardes a todos, empecemos.\n\n"
    "[00:00:18] Carlos (Backend): Del lado del backend, necesitamos un servicio.\n"
)


def test_normalize_parses_each_utterance() -> None:
    utterances = normalize(SAMPLE)

    assert len(utterances) == 2
    assert utterances[0].index == 0
    assert utterances[0].speaker == "Ana (Product Manager)"
    assert utterances[0].timestamp_ms == 3_000
    assert utterances[0].text == "Buenas tardes a todos, empecemos."

    assert utterances[1].speaker == "Carlos (Backend)"
    assert utterances[1].timestamp_ms == 18_000


def test_normalize_offsets_reconstruct_the_original_text() -> None:
    utterances = normalize(SAMPLE)

    for utterance in utterances:
        span = SAMPLE[utterance.start_char_offset : utterance.end_char_offset]
        assert utterance.text in span
        assert span.startswith("[")


def test_normalize_handles_multiline_utterances() -> None:
    transcript = (
        "[00:01:10] Carlos: Hay una dependencia importante: esto necesita que el equipo\n"
        "habilite las credenciales antes de que empecemos a integrar.\n\n"
        "[00:01:30] Ana: Anotado.\n"
    )
    utterances = normalize(transcript)

    assert len(utterances) == 2
    assert "dependencia importante" in utterances[0].text
    assert "habilite las credenciales" in utterances[0].text


def test_normalize_empty_transcript_returns_no_utterances() -> None:
    assert normalize("") == []
