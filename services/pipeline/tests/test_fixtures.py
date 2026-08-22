from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_sample_meeting_fixture_exists() -> None:
    sample = FIXTURES_DIR / "sample_meeting.txt"
    assert sample.exists()
    assert sample.read_text(encoding="utf-8").strip() != ""
