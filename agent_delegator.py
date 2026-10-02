from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class AgentAssignment:
    agent: str
    role: str
    task: str
    allowed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentDelegator:
    """MINH MINI multi-agent delegation boundary.

    Delegation decides WHO should do work. It does not execute work itself.
    """

    VERSION = "P1-AGENT-DELEGATION-1.0"

    ROLES = {
        "ollama": "local_reasoning",
        "gemini": "independent_review",
        "agent_reach": "external_tools",
        "minh": "orchestrator",
    }

    def assign(self, task: str, *, intent: str = "", tool: str = "") -> AgentAssignment:
        text = str(task or "").strip().lower()
        intent = str(intent or "").strip().lower()
        tool = str(tool or "").strip().lower()

        if not text:
            return AgentAssignment(
                "minh", self.ROLES["minh"], "", False,
                "Thiếu nhiệm vụ nên không được giao việc."
            )

        if tool in {"web", "web_context", "github", "youtube", "rss", "bilibili"}:
            return AgentAssignment(
                "agent_reach", self.ROLES["agent_reach"], task, True,
                "Nhiệm vụ cần capability/tool bên ngoài."
            )

        if any(x in text for x in ("phản biện", "review", "kiểm tra độc lập", "second opinion")):
            return AgentAssignment(
                "gemini", self.ROLES["gemini"], task, True,
                "Nhiệm vụ yêu cầu đánh giá độc lập."
            )

        if intent in {"action", "execute"} or tool == "action":
            return AgentAssignment(
                "minh", self.ROLES["minh"], task, True,
                "Hành động phải đi qua MINH MINI execution boundary."
            )

        return AgentAssignment(
            "ollama", self.ROLES["ollama"], task, True,
            "Nhiệm vụ suy luận mặc định dùng model local."
        )

    def self_check(self) -> dict[str, Any]:
        return {
            "module": "agent_delegator",
            "version": self.VERSION,
            "roles": dict(self.ROLES),
            "fail_closed": True,
        }


def create_agent_delegator() -> AgentDelegator:
    return AgentDelegator()
__all__ = ["AgentAssignment", "AgentDelegator", "create_agent_delegator"]


if __name__ == "__main__":
    import json

    d = create_agent_delegator()
    print(json.dumps(d.self_check(), ensure_ascii=False, indent=2))
    for sample in (
        ("Tìm thông tin mới trên web", "web", "web"),
        ("Phản biện kế hoạch", "chat", ""),
        ("Giải thích lỗi Python", "chat", ""),
        ("Mở ứng dụng", "action", "action"),
    ):
        print(json.dumps(
            d.assign(sample[0], intent=sample[1], tool=sample[2]).to_dict(),
            ensure_ascii=False,
        ))
