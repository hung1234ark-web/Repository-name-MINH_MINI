from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class ToolSelection:
    tool: str | None
    reason: str
    confidence: float
    allowed: bool
    advisory_only: bool = True
    version: str = "P11-1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ToolSelector:
    VERSION = "P11-1.0"

    def __init__(self):
        self.last_selection = None

    @staticmethod
    def _text(value):
        if value is None:
            return ""
        if isinstance(value, dict):
            parts = []
            for key, item in value.items():
                parts.append(str(key))
                parts.append(str(item))
            return " ".join(parts).strip().lower()
        if isinstance(value, (list, tuple)):
            return " ".join(str(item) for item in value).strip().lower()
        return str(value).strip().lower()

    def select(
        self,
        *,
        goal=None,
        plan=None,
        decision=None,
        result=None,
    ):
        text = " ".join(
            part
            for part in (
                self._text(goal),
                self._text(plan),
                self._text(decision),
                self._text(result),
            )
            if part
        )

        memory_terms = (
            "nhớ",
            "ghi nhớ",
            "lưu lại",
            "memory",
            "remember",
            "quên",
        )

        if any(term in text for term in memory_terms):
            return self._save(
                "memory",
                "Memory operation detected.",
                0.95,
            )

        time_terms = (
            "mấy giờ",
            "giờ hiện tại",
            "bây giờ là mấy giờ",
            "what time",
            "current time",
        )

        if any(term in text for term in time_terms):
            return self._save(
                "time",
                "Current time requested.",
                0.98,
            )

        date_terms = (
            "hôm nay",
            "ngày bao nhiêu",
            "ngày hôm nay",
            "today",
            "current date",
        )

        if any(term in text for term in date_terms):
            return self._save(
                "date",
                "Current date requested.",
                0.98,
            )

        web_terms = (
            "tìm trên mạng",
            "tìm trên web",
            "tìm thông tin trên mạng",
            "tìm thông tin trên web",
            "tra cứu trên mạng",
            "tra cứu trên web",
            "google",
            "website",
            "trang web",
            "tin tức",
            "giá",
            "tìm kiếm",
            "search",
            "latest",
            "news",
            "iphone",
        )

        if any(term in text for term in web_terms):
            return self._save(
                "web",
                "External web information requested.",
                0.90,
            )

        web_context_terms = (
            "nghiên cứu",
            "research",
            "phân tích trên web",
            "web context",
        )

        if any(term in text for term in web_context_terms):
            return self._save(
                "web_context",
                "Web context or research requested.",
                0.88,
            )

        action_terms = (
            "mở",
            "đóng",
            "chạy",
            "bật",
            "tắt",
            "click",
            "nhấn",
            "thực hiện",
            "execute",
        )

        if any(term in text for term in action_terms):
            return self._save(
                "action",
                "Executable action appears to be requested.",
                0.82,
            )

        if text:
            return self._save(
                "ollama",
                "No specialized tool matched; reasoning fallback selected.",
                0.55,
            )

        return self._save(
            None,
            "Insufficient information to select a tool.",
            0.0,
            allowed=False,
        )

    def _save(self, tool, reason, confidence, allowed=True):
        selection = ToolSelection(
            tool=tool,
            reason=reason,
            confidence=confidence,
            allowed=allowed,
        ).to_dict()

        self.last_selection = selection
        return dict(selection)


def create_tool_selector():
    return ToolSelector()
