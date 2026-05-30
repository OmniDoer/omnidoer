"""Challenge view metadata for Control Client."""


def challenge_view(origin: str, url: str, challenge_type: str) -> dict:
    return {
        "origin": origin,
        "url": url,
        "challenge_type": challenge_type,
        "completed_by_user_required": True,
        "not_for_llm": True,
    }
