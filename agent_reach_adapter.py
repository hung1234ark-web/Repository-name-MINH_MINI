from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentReachResult:
    success: bool
    capability: str
    message: str
    data: Any = None
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentReachAdapter:
    """
    Stable adapter between MINH MINI and the Agent Reach CLI.

    The adapter never guesses capability readiness from keywords. Capability
    state is taken from the structured output of `agent-reach doctor --json`.
    """

    VERSION = "AGENT-REACH-ADAPTER-2.0"

    def __init__(self, executable: str | None = None, timeout: int = 60):
        self.timeout = timeout
        self.executable = self._resolve_executable(executable)

    # ---------------------------------------------------------
    # PATH / AVAILABILITY
    # ---------------------------------------------------------

    def _resolve_executable(self, executable: str | None) -> str | None:
        candidates: list[Path] = []

        if executable:
            candidates.append(Path(executable))

        env_path = os.environ.get("AGENT_REACH_EXE")
        if env_path:
            candidates.append(Path(env_path))

        home = Path.home()
        candidates.extend(
            [
                home / ".agent-reach-venv" / "Scripts" / "agent-reach.exe",
                home / ".agent-reach-venv" / "Scripts" / "agent-reach",
            ]
        )

        for candidate in candidates:
            try:
                if candidate.exists() and candidate.is_file():
                    return str(candidate)
            except OSError:
                continue

        return None

    def available(self) -> bool:
        return bool(self.executable)

    def describe(self) -> dict[str, Any]:
        return {
            "provider": "agent_reach",
            "version": self.VERSION,
            "available": self.available(),
            "executable": self.executable or "",
        }

    # ---------------------------------------------------------
    # EXECUTION
    # ---------------------------------------------------------

    def _run(self, *args: str, timeout: int | None = None) -> AgentReachResult:
        if not self.executable:
            return AgentReachResult(
                success=False,
                capability="",
                message="Agent Reach chưa khả dụng.",
                error="executable_not_found",
                metadata=self.describe(),
            )

        command = [self.executable, *args]

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout or self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return AgentReachResult(
                success=False,
                capability="",
                message="Agent Reach hết thời gian chờ.",
                error="timeout",
                metadata={**self.describe(), "command": command},
            )
        except OSError as exc:
            return AgentReachResult(
                success=False,
                capability="",
                message="Không thể khởi chạy Agent Reach.",
                error=str(exc),
                metadata={**self.describe(), "command": command},
            )
        except Exception as exc:
            return AgentReachResult(
                success=False,
                capability="",
                message="Agent Reach gặp lỗi khi thực thi.",
                error=str(exc),
                metadata={**self.describe(), "command": command},
            )

        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()

        if completed.returncode != 0:
            return AgentReachResult(
                success=False,
                capability="",
                message="Agent Reach trả về lỗi.",
                error=stderr or stdout or f"exit_code={completed.returncode}",
                metadata={
                    **self.describe(),
                    "command": command,
                    "returncode": completed.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                },
            )

        return AgentReachResult(
            success=True,
            capability="",
            message=stdout or "Agent Reach thực thi thành công.",
            data=stdout,
            metadata={
                **self.describe(),
                "command": command,
                "returncode": completed.returncode,
                "stderr": stderr,
            },
        )

    # ---------------------------------------------------------
    # BASIC CAPABILITIES
    # ---------------------------------------------------------

    def version(self) -> AgentReachResult:
        result = self._run("version")
        result.capability = "version"
        return result

    def help(self) -> AgentReachResult:
        result = self._run("--help")
        result.capability = "help"
        return result

    def doctor(self) -> AgentReachResult:
        result = self._run("doctor")
        result.capability = "doctor"
        return result

    def doctor_json(self) -> AgentReachResult:
        result = self._run("doctor", "--json")
        result.capability = "doctor_json"
        return result

    # ---------------------------------------------------------
    # SAFE CAPABILITY DISCOVERY
    # ---------------------------------------------------------

    def capability_status(self) -> AgentReachResult:
        """
        Return the real Agent Reach capability registry.

        Readiness rules:
        - status == "ok" AND active_backend is present -> ready
        - status == "warn" or "off" -> not ready
        - no keyword heuristics
        - no automatic installation
        """

        result = self.doctor_json()

        if not result.success:
            result.message = (
                "Không lấy được trạng thái capability của Agent Reach."
            )
            return result

        raw = str(result.data or "")

        try:
            doctor_data = json.loads(raw)
        except json.JSONDecodeError as exc:
            result.success = False
            result.message = "Agent Reach doctor --json trả về dữ liệu không hợp lệ."
            result.error = f"invalid_doctor_json: {exc}"
            result.metadata["raw_output"] = raw
            return result

        if not isinstance(doctor_data, dict):
            result.success = False
            result.message = "Agent Reach doctor --json không trả về object."
            result.error = "invalid_doctor_shape"
            result.metadata["raw_output"] = raw
            return result

        registry: dict[str, dict[str, Any]] = {}

        for name, info in doctor_data.items():
            if not isinstance(info, dict):
                continue

            status = str(info.get("status") or "").lower()
            active_backend = info.get("active_backend")
            active_backend = (
                str(active_backend).strip()
                if active_backend is not None
                else ""
            )

            ready = status == "ok" and bool(active_backend)

            registry[name] = {
                "status": status,
                "ready": ready,
                "active_backend": active_backend,
                "name": info.get("name", name),
                "message": info.get("message", ""),
                "tier": info.get("tier"),
                "backends": info.get("backends", []),
            }

        active_names = [
            name for name, info in registry.items() if info["ready"]
        ]

        result.data = {
            "registry": registry,
            "active_names": active_names,
            "active_count": len(active_names),
        }
        result.message = (
            f"Đã đọc trạng thái Agent Reach thật: "
            f"{len(active_names)} capability đang sẵn sàng."
        )
        result.metadata["registry"] = registry

        return result

    def is_capability_ready(self, capability: str) -> bool:
        result = self.capability_status()

        if not result.success:
            return False

        registry = result.data.get("registry", {})
        info = registry.get(str(capability).strip().lower())

        return bool(info and info.get("ready") is True)

    # ---------------------------------------------------------
    # SAFE WEB / RSS READERS
    # ---------------------------------------------------------

    def read_web(self, url: str) -> AgentReachResult:
        url = str(url or "").strip()
        if not url:
            return AgentReachResult(
                success=False,
                capability="web",
                message="Thiếu URL.",
                error="missing_url",
                metadata=self.describe(),
            )

        if not self.is_capability_ready("web"):
            return AgentReachResult(
                success=False,
                capability="web",
                message="Agent Reach Web chưa sẵn sàng.",
                error="capability_not_ready",
                metadata=self.describe(),
            )

        result = self._run(
            "exec",
            "curl",
            "-s",
            f"https://r.jina.ai/{url}",
        )
        result.capability = "web"
        return result

    def read_rss(self, feed_url: str, limit: int = 10) -> AgentReachResult:
        feed_url = str(feed_url or "").strip()
        limit = max(1, min(int(limit), 50))

        if not feed_url:
            return AgentReachResult(
                success=False,
                capability="rss",
                message="Thiếu RSS URL.",
                error="missing_feed_url",
                metadata=self.describe(),
            )

        if not self.is_capability_ready("rss"):
            return AgentReachResult(
                success=False,
                capability="rss",
                message="Agent Reach RSS chưa sẵn sàng.",
                error="capability_not_ready",
                metadata=self.describe(),
            )

        script = (
            "import feedparser, json, sys\n"
            "url = sys.argv[1]\n"
            "limit = int(sys.argv[2])\n"
            "feed = feedparser.parse(url)\n"
            "items = []\n"
            "for e in feed.entries[:limit]:\n"
            "    items.append({\n"
            "        'title': getattr(e, 'title', ''),\n"
            "        'link': getattr(e, 'link', ''),\n"
            "        'summary': getattr(e, 'summary', ''),\n"
            "    })\n"
            "print(json.dumps(items, ensure_ascii=False))\n"
        )

        result = self._run(
            "exec",
            "python",
            "-c",
            script,
            feed_url,
            str(limit),
        )
        result.capability = "rss"
        return result


# -------------------------------------------------------------
# MODULE-LEVEL API
# -------------------------------------------------------------

_adapter: AgentReachAdapter | None = None


def get_adapter() -> AgentReachAdapter:
    global _adapter

    if _adapter is None:
        _adapter = AgentReachAdapter()

    return _adapter


def available() -> bool:
    return get_adapter().available()


def describe() -> dict[str, Any]:
    return get_adapter().describe()


def version() -> AgentReachResult:
    return get_adapter().version()


def doctor() -> AgentReachResult:
    return get_adapter().doctor()


def doctor_json() -> AgentReachResult:
    return get_adapter().doctor_json()


def capability_status() -> AgentReachResult:
    return get_adapter().capability_status()


def self_check() -> dict[str, Any]:
    adapter = get_adapter()

    return {
        "module": "agent_reach_adapter",
        "version": AgentReachAdapter.VERSION,
        "available": adapter.available(),
        "executable": adapter.executable or "",
    }


if __name__ == "__main__":
    print(json.dumps(self_check(), ensure_ascii=False, indent=2))
    print()
    print("=== AGENT REACH VERSION ===")
    print(version().message)
    print()
    print("=== AGENT REACH CAPABILITIES ===")
    result = capability_status()
    print(json.dumps(result.data, ensure_ascii=False, indent=2))
