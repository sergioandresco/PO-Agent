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


REAL_MEETING_TRANSCRIPT = (
    "Asunto: Kick-off Integracion\n"
    "Participantes:\n"
    " Carlos Mendoza: Lider de Logistica, Dislicores\n"
    " Fecha de la reunion: 21 de agosto de 2026\n"
    "[Inicio de la transcripcion]\n"
    "Carlos: Hola, David. Gracias por el espacio.\n"
    "David: Hola, Carlos. Entendido.\n"
    "[Fin de la transcripcion]\n"
    "Acuerdos y Definiciones de Negocio\n"
    " Estado Comprometido: Documento con aprobacion financiera.\n"
)


def test_normalize_handles_untimestamped_speaker_colon_text() -> None:
    utterances = normalize(REAL_MEETING_TRANSCRIPT)

    assert len(utterances) == 2
    assert utterances[0].speaker == "Carlos"
    assert utterances[0].timestamp_ms is None
    assert utterances[0].text == "Hola, David. Gracias por el espacio."
    assert utterances[1].speaker == "David"


def test_normalize_excludes_header_and_footer_outside_transcript_markers() -> None:
    utterances = normalize(REAL_MEETING_TRANSCRIPT)

    all_text = " ".join(u.text for u in utterances)
    all_speakers = {u.speaker for u in utterances}
    assert "Lider de Logistica" not in all_text
    assert "Estado Comprometido" not in all_text
    assert "Fecha de la reunion" not in all_speakers


MEET_STYLE_TRANSCRIPT = (
    "Ana Garcia  0:03\n"
    "Hola a todos, empecemos con la reunion de hoy.\n\n"
    "Carlos Lopez  0:15\n"
    "Perfecto, del lado del backend tenemos listo el servicio.\n\n"
    "Ana Garcia  0:32\n"
    "Genial, entonces seguimos con el siguiente punto.\n"
)


def test_normalize_falls_back_to_meet_style_header_when_no_colon_dialogue() -> None:
    utterances = normalize(MEET_STYLE_TRANSCRIPT)

    assert len(utterances) == 3
    assert utterances[0].speaker == "Ana Garcia"
    assert utterances[0].timestamp_ms == 3_000
    assert utterances[0].text == "Hola a todos, empecemos con la reunion de hoy."
    assert utterances[1].speaker == "Carlos Lopez"
    assert utterances[1].timestamp_ms == 15_000
