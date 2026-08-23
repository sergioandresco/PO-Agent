from .types import Utterance


def format_utterances_for_prompt(utterances: list[Utterance]) -> str:
    return "\n".join(f"[{u.index}] {u.speaker}: {u.text}" for u in utterances)
