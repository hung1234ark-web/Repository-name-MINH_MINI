from __future__ import annotations

import json

from agent_reach_adapter import AgentReachAdapter


def test_capability_status_uses_doctor_json() -> None:
    adapter = AgentReachAdapter(executable="fake-agent-reach")

    payload = {
        "web": {
            "status": "ok",
            "active_backend": "Jina Reader",
            "message": "ready",
        },
        "rss": {
            "status": "ok",
            "active_backend": "feedparser",
            "message": "ready",
        },
        "youtube": {
            "status": "off",
            "active_backend": None,
            "message": "yt-dlp not installed",
        },
        "github": {
            "status": "warn",
            "active_backend": None,
            "message": "gh CLI not installed",
        },
    }

    class Result:
        success = True
        data = json.dumps(payload)
        message = ""
        error = ""
        metadata = {}

    adapter.doctor_json = lambda: Result()  # type: ignore[method-assign]

    result = adapter.capability_status()

    assert result.success is True
    assert result.data["active_names"] == ["web", "rss"]
    assert result.data["active_count"] == 2
    assert result.data["registry"]["web"]["ready"] is True
    assert result.data["registry"]["youtube"]["ready"] is False
    assert result.data["registry"]["github"]["ready"] is False


def test_invalid_doctor_json_fails_closed() -> None:
    adapter = AgentReachAdapter(executable="fake-agent-reach")

    class Result:
        success = True
        data = "{invalid json"
        message = ""
        error = ""
        metadata = {}

    adapter.doctor_json = lambda: Result()  # type: ignore[method-assign]

    result = adapter.capability_status()

    assert result.success is False
    assert result.error.startswith("invalid_doctor_json:")


if __name__ == "__main__":
    test_capability_status_uses_doctor_json()
    test_invalid_doctor_json_fails_closed()
    print("AGENT REACH ADAPTER TEST: PASS")
