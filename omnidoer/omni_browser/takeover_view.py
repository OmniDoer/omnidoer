"""Human Takeover view metadata."""


def takeover_view(origin: str, url: str, reason: str) -> dict:
    return {
        "origin": origin,
        "url": url,
        "reason": reason,
        "agent_status": "paused",
        "control_owner": "user",
        "not_for_llm": True,
    }
