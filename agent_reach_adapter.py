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
    Adapter độc lập cho Agent Reach.

    MINH MINI không phụ thuộc trực tiếp vào implementation bên trong
    Agent Reach. Adapter này chỉ giao tiếp với executable agent-reach.exe.
    """

    VERSION = "AGENT-REACH-ADAPTER-1.0"

    def __init__(self, executable: str | None = None, timeout: int = 60):
        self.timeout = timeout
        self.executable = self._resolve_executable(executable)

    # ---------------------------------------------------------
    # PATH / AVAILABILITY
    # ---------------------------------------------------------

    def _resolve_executable(self, executable: str | None) -> str | None:
        candidates = []

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
                metadata={
                    **self.describe(),
                    "command": command,
                },
            )
        except OSError as exc:
            return AgentReachResult(
                success=False,
                capability="",
                message="Không thể khởi chạy Agent Reach.",
                error=str(exc),
                metadata={
                    **self.describe(),
                    "command": command,
                },
            )
        except Exception as exc:
            return AgentReachResult(
                success=False,
                capability="",
                message="Agent Reach gặp lỗi khi thực thi.",
                error=str(exc),
                metadata={
                    **self.describe(),
                    "command": command,
                },
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

    # ---------------------------------------------------------
    # SAFE CAPABILITY DISCOVERY
    # ---------------------------------------------------------

    def capability_status(self) -> AgentReachResult:
        """
        Kiểm tra capability mà không tự cài thêm dependency.
        """

        result = self.doctor()

        if not result.success:
            result.message = "Không lấy được trạng thái capability của Agent Reach."
            return result

        text_output = str(result.data or "")

        capabilities = {
            "youtube": False,
            "web": False,
            "rss": False,
            "v2ex": False,
            "bilibili": False,
            "github": False,
            "exa": False,
        }

        lower = text_output.lower()

        # Chỉ đánh dấu capability khi doctor không báo thiếu dependency
        # rõ ràng. Không tự suy đoán capability.
        if "jina" in lower or "web" in lower:
            capabilities["web"] = True

        if "rss" in lower or "atom" in lower:
            capabilities["rss"] = True

        if "v2ex" in lower and (
            "active" in lower or "ok" in lower or "ready" in lower
        ):
            capabilities["v2ex"] = True

        if "bilibili" in lower and (
            "active" in lower or "ok" in lower or "ready" in lower
        ):
            capabilities["bilibili"] = True

        # YouTube chỉ ready nếu doctor không báo thiếu JS runtime.
        youtube_missing_runtime = (
            "javascript runtime" in lower
            or "js runtime" in lower
            or "missing" in lower and "runtime" in lower
        )

        if "youtube" in lower and not youtube_missing_runtime:
            capabilities["youtube"] = True

        if "github" in lower and not (
            "not installed" in lower or "missing" in lower
        ):
            capabilities["github"] = True

        if "exa" in lower and not (
            "not installed" in lower or "missing" in lower
        ):
            capabilities["exa"] = True

        result.data = capabilities
        result.message = "Đã kiểm tra capability Agent Reach."
        result.metadata["capabilities"] = capabilities

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
