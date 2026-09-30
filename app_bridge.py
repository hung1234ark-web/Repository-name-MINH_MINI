# ============================================================
# MINH MINI — APP BRIDGE FINAL
# Cầu nối điều khiển Windows
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import os
import shutil
import subprocess
import webbrowser
import urllib.parse


# ============================================================
# PATHS
# ============================================================

HOME = Path.home()

DESKTOP = HOME / "Desktop"
DOWNLOADS = HOME / "Downloads"
DOCUMENTS = HOME / "Documents"
PICTURES = HOME / "Pictures"
VIDEOS = HOME / "Videos"
MUSIC = HOME / "Music"

THIS_PC = Path("C:\\")


# ============================================================
# RESULT
# ============================================================

@dataclass
class BridgeResult:

    success: bool = False

    action: str = ""

    target: str = ""

    response: str = ""

    error: str = ""

    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)


# ============================================================
# HELPERS
# ============================================================

def clean_text(value: Any) -> str:

    if value is None:
        return ""

    return str(value).strip()


def normalize(value: Any) -> str:

    return clean_text(value).lower()


def path_exists(path: Path) -> bool:

    try:
        return path.exists()

    except Exception:
        return False


def run_process(
    program: str,
    *args: str,
    timeout: int = 15,
    wait: bool = False,
) -> BridgeResult:

    command = [
        program,
        *args,
    ]

    try:

        if wait:

            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )

            if completed.returncode == 0:

                return BridgeResult(
                    success=True,
                    action="process",
                    target=program,
                    response=(
                        completed.stdout.strip()
                        or f"Đã chạy {program}."
                    ),
                    metadata={
                        "returncode": completed.returncode,
                    },
                )

            error = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"Process trả về mã {completed.returncode}."
            )

            return BridgeResult(
                success=False,
                action="process",
                target=program,
                response="",
                error=error,
                metadata={
                    "returncode": completed.returncode,
                },
            )

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            shell=False,
        )

        return BridgeResult(
            success=True,
            action="process",
            target=program,
            response=f"Đã khởi chạy {program}.",
            metadata={
                "pid": process.pid,
            },
        )

    except FileNotFoundError:

        return BridgeResult(
            success=False,
            action="process",
            target=program,
            error=f"Không tìm thấy chương trình: {program}",
        )

    except subprocess.TimeoutExpired:

        return BridgeResult(
            success=False,
            action="process",
            target=program,
            error="Chương trình chạy quá thời gian cho phép.",
        )

    except Exception as exc:

        return BridgeResult(
            success=False,
            action="process",
            target=program,
            error=str(exc),
        )


# ============================================================
# WINDOWS TARGETS
# ============================================================

TARGETS: dict[str, dict[str, Any]] = {

    "google": {
        "type": "url",
        "value": "https://www.google.com",
    },

    "youtube": {
        "type": "url",
        "value": "https://www.youtube.com",
    },

    "facebook": {
        "type": "url",
        "value": "https://www.facebook.com",
    },

    "notepad": {
        "type": "program",
        "program": "notepad.exe",
    },

    "calculator": {
        "type": "program",
        "program": "calc.exe",
    },

    "calc": {
        "type": "program",
        "program": "calc.exe",
    },

    "paint": {
        "type": "program",
        "program": "mspaint.exe",
    },

    "explorer": {
        "type": "program",
        "program": "explorer.exe",
    },

    "file explorer": {
        "type": "program",
        "program": "explorer.exe",
    },

    "desktop": {
        "type": "path",
        "value": DESKTOP,
    },

    "downloads": {
        "type": "path",
        "value": DOWNLOADS,
    },

    "documents": {
        "type": "path",
        "value": DOCUMENTS,
    },

    "pictures": {
        "type": "path",
        "value": PICTURES,
    },

    "videos": {
        "type": "path",
        "value": VIDEOS,
    },

    "music": {
        "type": "path",
        "value": MUSIC,
    },

    "this pc": {
        "type": "path",
        "value": THIS_PC,
    },
}


ALIASES = {

    "google": "google",
    "gg": "google",

    "youtube": "youtube",
    "yt": "youtube",

    "facebook": "facebook",
    "fb": "facebook",

    "notepad": "notepad",
    "note": "notepad",
    "notepad windows": "notepad",

    "calculator": "calculator",
    "cal": "calculator",
    "máy tính": "calculator",

    "paint": "paint",
    "ms paint": "paint",

    "explorer": "explorer",
    "file explorer": "file explorer",
    "file manager": "explorer",
    "trình quản lý tệp": "explorer",

    "desktop": "desktop",
    "màn hình chính": "desktop",

    "downloads": "downloads",
    "download": "downloads",
    "tải xuống": "downloads",

    "documents": "documents",
    "document": "documents",
    "tài liệu": "documents",

    "pictures": "pictures",
    "picture": "pictures",
    "ảnh": "pictures",

    "videos": "videos",
    "video": "videos",

    "music": "music",
    "nhạc": "music",

    "this pc": "this pc",
    "my computer": "this pc",
    "máy tính này": "this pc",
}


# ============================================================
# TARGET RESOLUTION
# ============================================================

def resolve_target(
    target: str,
) -> tuple[str, dict[str, Any] | None]:

    raw = clean_text(target)

    key = normalize(raw)

    key = ALIASES.get(
        key,
        key,
    )

    info = TARGETS.get(
        key
    )

    return key, info


# ============================================================
# OPEN URL
# ============================================================

def open_url(
    url: str,
) -> BridgeResult:

    url = clean_text(url)

    if not url:

        return BridgeResult(
            success=False,
            action="open_url",
            error="URL trống.",
        )

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):

        url = "https://" + url

    try:

        ok = webbrowser.open(
            url,
            new=2,
        )

        if ok:

            return BridgeResult(
                success=True,
                action="open_url",
                target=url,
                response=f"Đã mở {url}.",
                metadata={
                    "url": url,
                },
            )

        return BridgeResult(
            success=False,
            action="open_url",
            target=url,
            error="Windows không xác nhận mở trình duyệt.",
        )

    except Exception as exc:

        return BridgeResult(
            success=False,
            action="open_url",
            target=url,
            error=str(exc),
        )


# ============================================================
# OPEN PATH
# ============================================================

def open_path(
    path: Path,
) -> BridgeResult:

    try:

        if not path.exists():

            return BridgeResult(
                success=False,
                action="open_path",
                target=str(path),
                error=f"Không tìm thấy thư mục: {path}",
            )

        result = subprocess.Popen(
            [
                "explorer.exe",
                str(path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            shell=False,
        )

        return BridgeResult(
            success=True,
            action="open_path",
            target=str(path),
            response=f"Đã mở {path}.",
            metadata={
                "pid": result.pid,
            },
        )

    except Exception as exc:

        return BridgeResult(
            success=False,
            action="open_path",
            target=str(path),
            error=str(exc),
        )


# ============================================================
# OPEN PROGRAM
# ============================================================

def open_program(
    program: str,
) -> BridgeResult:

    return run_process(
        program
    )


# ============================================================
# OPEN TARGET
# ============================================================

def open_target(
    target: str,
) -> BridgeResult:

    key, info = resolve_target(
        target
    )

    if info is None:

        return BridgeResult(
            success=False,
            action="open",
            target=target,
            error=(
                f"Minh chưa biết cách mở mục: {target}"
            ),
        )

    target_type = info.get(
        "type"
    )

    if target_type == "url":

        return open_url(
            info["value"]
        )

    if target_type == "program":

        return open_program(
            info["program"]
        )

    if target_type == "path":

        return open_path(
            Path(
                info["value"]
            )
        )

    return BridgeResult(
        success=False,
        action="open",
        target=target,
        error="Loại target không được hỗ trợ.",
    )


# ============================================================
# SEARCH
# ============================================================

def search_google(
    query: str,
) -> BridgeResult:

    query = clean_text(query)

    if not query:

        return BridgeResult(
            success=False,
            action="search_google",
            error="Từ khóa tìm kiếm đang trống.",
        )

    url = (
        "https://www.google.com/search?q="
        + urllib.parse.quote_plus(query)
    )

    return open_url(
        url
    )


def search_youtube(
    query: str,
) -> BridgeResult:

    query = clean_text(query)

    if not query:

        return BridgeResult(
            success=False,
            action="search_youtube",
            error="Từ khóa tìm kiếm đang trống.",
        )

    url = (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote_plus(query)
    )

    return open_url(
        url
    )


# ============================================================
# CLOSE APPLICATION
# ============================================================

PROGRAM_PROCESS_NAMES = {

    "notepad": "notepad.exe",
    "calculator": "CalculatorApp.exe",
    "calc": "CalculatorApp.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
}


def close_program(
    target: str,
) -> BridgeResult:

    key, info = resolve_target(
        target
    )

    process_name = PROGRAM_PROCESS_NAMES.get(
        key
    )

    if not process_name:

        if info and info.get("type") == "program":

            program = clean_text(
                info.get("program")
            )

            if program:
                process_name = program

    if not process_name:

        return BridgeResult(
            success=False,
            action="close",
            target=target,
            error=(
                f"Minh chưa biết tiến trình cần đóng: {target}"
            ),
        )

    try:

        completed = subprocess.run(
            [
                "taskkill",
                "/IM",
                process_name,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )

        if completed.returncode == 0:

            return BridgeResult(
                success=True,
                action="close",
                target=target,
                response=f"Đã đóng {target}.",
                metadata={
                    "process": process_name,
                    "returncode": completed.returncode,
                },
            )

        output = (
            completed.stderr.strip()
            or completed.stdout.strip()
        )

        # taskkill có thể trả mã khác 0 khi process
        # chưa tồn tại. Không giả thành công.
        return BridgeResult(
            success=False,
            action="close",
            target=target,
            error=(
                output
                or f"Không thể đóng {target}."
            ),
            metadata={
                "process": process_name,
                "returncode": completed.returncode,
            },
        )

    except Exception as exc:

        return BridgeResult(
            success=False,
            action="close",
            target=target,
            error=str(exc),
        )


# ============================================================
# OPEN FOLDER SHORTCUTS
# ============================================================

def open_desktop() -> BridgeResult:

    return open_path(
        DESKTOP
    )


def open_downloads() -> BridgeResult:

    return open_path(
        DOWNLOADS
    )


def open_documents() -> BridgeResult:

    return open_path(
        DOCUMENTS
    )


def open_pictures() -> BridgeResult:

    return open_path(
        PICTURES
    )


def open_videos() -> BridgeResult:

    return open_path(
        VIDEOS
    )


def open_music() -> BridgeResult:

    return open_path(
        MUSIC
    )


def open_this_pc() -> BridgeResult:

    return open_path(
        THIS_PC
    )


# ============================================================
# DISPATCH
# ============================================================

def dispatch(
    action: str = "",
    target: str = "",
    query: str = "",
    command: str = "",
) -> BridgeResult:

    action_key = normalize(
        action
    )

    target_text = clean_text(
        target
    )

    query_text = clean_text(
        query
    )

    command_text = clean_text(
        command
    )

    # --------------------------------------------------------
    # SEARCH GOOGLE
    # --------------------------------------------------------

    if action_key in {
        "search_google",
        "google_search",
        "google",
        "search",
    }:

        if query_text:

            return search_google(
                query_text
            )

        if target_text:

            return search_google(
                target_text
            )

    # --------------------------------------------------------
    # SEARCH YOUTUBE
    # --------------------------------------------------------

    if action_key in {
        "search_youtube",
        "youtube_search",
    }:

        if query_text:

            return search_youtube(
                query_text
            )

        if target_text:

            return search_youtube(
                target_text
            )

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    if action_key in {
        "close",
        "quit",
        "exit",
        "kill",
    }:

        return close_program(
            target_text
        )

    # --------------------------------------------------------
    # OPEN
    # --------------------------------------------------------

    if action_key in {
        "open",
        "launch",
        "start",
        "go_to",
        "goto",
    }:

        if target_text:

            return open_target(
                target_text
            )

        if command_text:

            return open_target(
                command_text
            )

        return BridgeResult(
            success=False,
            action="open",
            error="Chưa có mục cần mở.",
        )

    # --------------------------------------------------------
    # DIRECT URL
    # --------------------------------------------------------

    if action_key in {
        "open_url",
        "url",
    }:

        return open_url(
            target_text
            or query_text
        )

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    return BridgeResult(
        success=False,
        action=action_key,
        target=target_text,
        error=(
            f"Hành động Windows chưa được hỗ trợ: "
            f"{action or command or target}"
        ),
    )


# ============================================================
# COMPATIBILITY API
# ============================================================

def handle_action(
    command: str = "",
    action: str = "",
    target: str = "",
    query: str = "",
    **kwargs: Any,
) -> dict[str, Any]:

    result = dispatch(
        action=action,
        target=target,
        query=query,
        command=command,
    )

    return result.to_dict()


def execute(
    command: str = "",
    action: str = "",
    target: str = "",
    query: str = "",
    **kwargs: Any,
) -> dict[str, Any]:

    return handle_action(
        command=command,
        action=action,
        target=target,
        query=query,
        **kwargs,
    )


def run(
    command: str = "",
    action: str = "",
    target: str = "",
    query: str = "",
    **kwargs: Any,
) -> dict[str, Any]:

    return handle_action(
        command=command,
        action=action,
        target=target,
        query=query,
        **kwargs,
    )


def action(
    command: str = "",
    action: str = "",
    target: str = "",
    query: str = "",
    **kwargs: Any,
) -> dict[str, Any]:

    return handle_action(
        command=command,
        action=action,
        target=target,
        query=query,
        **kwargs,
    )


# ============================================================
# STATUS
# ============================================================

def available_targets() -> list[str]:

    return sorted(
        TARGETS.keys()
    )


def describe() -> dict[str, Any]:

    return {
        "module": "app_bridge",
        "name": "MINH MINI APP BRIDGE FINAL",
        "platform": "Windows",
        "targets": available_targets(),
        "features": [
            "open websites",
            "open Windows applications",
            "open folders",
            "Google search",
            "YouTube search",
            "close supported applications",
            "real execution result",
            "success/failure reporting",
        ],
    }


# ============================================================
# SELF CHECK
# ============================================================

def self_check() -> dict[str, bool]:

    checks: dict[str, bool] = {}

    # --------------------------------------------------------
    # Resolve aliases
    # --------------------------------------------------------

    key, info = resolve_target(
        "máy tính"
    )

    checks["resolve_calculator"] = (
        key == "calculator"
        and info is not None
    )

    key, info = resolve_target(
        "YouTube"
    )

    checks["resolve_youtube"] = (
        key == "youtube"
        and info is not None
    )

    # --------------------------------------------------------
    # URL generation
    # --------------------------------------------------------

    parsed_google = (
        "https://www.google.com/search?q="
        + urllib.parse.quote_plus(
            "iphone mới"
        )
    )

    checks["google_url"] = (
        parsed_google.startswith(
            "https://www.google.com/search?q="
        )
    )

    # --------------------------------------------------------
    # Target paths
    # --------------------------------------------------------

    checks["desktop_path"] = (
        isinstance(
            DESKTOP,
            Path,
        )
    )

    checks["downloads_path"] = (
        isinstance(
            DOWNLOADS,
            Path,
        )
    )

    # --------------------------------------------------------
    # Result serialization
    # --------------------------------------------------------

    result = BridgeResult(
        success=True,
        action="test",
        target="test",
        response="ok",
    )

    result_dict = result.to_dict()

    checks["result_serialization"] = (
        result_dict.get("success") is True
        and result_dict.get("response") == "ok"
    )

    # --------------------------------------------------------
    # Unknown target must NOT claim success
    # --------------------------------------------------------

    unknown = open_target(
        "__MINH_MINI_UNKNOWN_TARGET__"
    )

    checks["unknown_target_safe"] = (
        unknown.success is False
        and bool(unknown.error)
    )

    return checks


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "MINH MINI — APP BRIDGE FINAL"
    )

    print(
        f"Windows targets: {len(TARGETS)}"
    )

    checks = self_check()

    passed = 0

    for name, ok in checks.items():

        print(
            f"[{'PASS' if ok else 'FAIL'}] {name}"
        )

        if ok:
            passed += 1

    print(
        f"RESULT: {passed}/{len(checks)} checks."
    )