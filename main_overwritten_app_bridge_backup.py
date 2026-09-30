# ============================================================
# MINH MINI / ÁNH
# APP BRIDGE — COMPLETE EXECUTOR
# Windows App / Folder / Website / Path
#
# Architecture:
# Understanding -> Central Router -> App Executor
#
# App Bridge KHÔNG làm bộ não hiểu ý.
# Nó chỉ nhận lệnh đã được chuẩn hóa và thực thi an toàn.
# ============================================================

from __future__ import annotations

import os
import re
import shutil
import subprocess
import unicodedata
import webbrowser
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote_plus


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


# ============================================================
# WINDOWS APPLICATIONS
# ============================================================

APP_COMMANDS = {
    "notepad": ["notepad.exe"],
    "note": ["notepad.exe"],

    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "máy tính": ["calc.exe"],
    "may tinh": ["calc.exe"],

    "paint": ["mspaint.exe"],

    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "file": ["explorer.exe"],
}


# ============================================================
# WEBSITES
# ============================================================

WEBSITES = {
    "google": "https://www.google.com",
    "chrome": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
}


# ============================================================
# WINDOWS FOLDERS
# ============================================================

FOLDERS = {
    "desktop": DESKTOP,
    "màn hình desktop": DESKTOP,
    "man hinh desktop": DESKTOP,

    "downloads": DOWNLOADS,
    "download": DOWNLOADS,
    "tải xuống": DOWNLOADS,
    "tai xuong": DOWNLOADS,

    "documents": DOCUMENTS,
    "document": DOCUMENTS,
    "tài liệu": DOCUMENTS,
    "tai lieu": DOCUMENTS,

    "pictures": PICTURES,
    "picture": PICTURES,
    "ảnh": PICTURES,
    "anh": PICTURES,

    "videos": VIDEOS,
    "video": VIDEOS,
    "video của tôi": VIDEOS,
    "video cua toi": VIDEOS,

    "music": MUSIC,
    "nhạc": MUSIC,
    "nhac": MUSIC,

    "home": HOME,
    "thư mục chính": HOME,
    "thu muc chinh": HOME,
}


# ============================================================
# ALIASES
# ============================================================

ALIASES = {
    # Notepad
    "notepad": "notepad",
    "note": "notepad",
    "notpad": "notepad",
    "notepd": "notepad",
    "notepa": "notepad",
    "trình soạn thảo": "notepad",
    "trinh soan thao": "notepad",
    "sổ tay": "notepad",
    "so tay": "notepad",

    # Calculator
    "calculator": "calculator",
    "calc": "calculator",
    "calcuator": "calculator",
    "calculater": "calculator",
    "calcutor": "calculator",
    "máy tính": "calculator",
    "may tinh": "calculator",
    "may tin": "calculator",

    # Paint
    "paint": "paint",
    "mở vẽ": "paint",
    "mo ve": "paint",

    # Explorer
    "explorer": "explorer",
    "file explorer": "explorer",
    "file": "explorer",
    "trình quản lý file": "explorer",
    "trinh quan ly file": "explorer",
    "quản lý file": "explorer",
    "quan ly file": "explorer",

    # Desktop
    "desktop": "desktop",
    "màn hình desktop": "desktop",
    "man hinh desktop": "desktop",
    "màn hình chính": "desktop",
    "man hinh chinh": "desktop",

    # Downloads
    "downloads": "downloads",
    "download": "downloads",
    "dowloads": "downloads",
    "downlaods": "downloads",
    "donwloads": "downloads",
    "tải xuống": "downloads",
    "tai xuong": "downloads",

    # Documents
    "documents": "documents",
    "document": "documents",
    "tài liệu": "documents",
    "tai lieu": "documents",

    # Pictures
    "pictures": "pictures",
    "picture": "pictures",
    "ảnh": "pictures",
    "anh": "pictures",

    # Videos
    "videos": "videos",
    "video": "videos",
    "video của tôi": "videos",
    "video cua toi": "videos",

    # Music
    "music": "music",
    "nhạc": "music",
    "nhac": "music",

    # Home
    "home": "home",
    "thư mục chính": "home",
    "thu muc chinh": "home",

    # Websites
    "google": "google",
    "gogle": "google",
    "googel": "google",
    "ggogle": "google",

    "chrome": "chrome",

    "youtube": "youtube",
    "youtub": "youtube",
    "yutube": "youtube",
    "you tube": "youtube",

    "facebook": "facebook",
    "facebok": "facebook",
    "facebookk": "facebook",
}


# ============================================================
# ACTION WORDS
# ============================================================

OPEN_WORDS = {
    "mo",
    "mở",
    "open",
    "vao",
    "vào",
    "truy cap",
    "truy cập",
    "bat",
    "bật",
}

SEARCH_WORDS = {
    "tim",
    "tìm",
    "search",
    "tim kiem",
    "tìm kiếm",
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    if text is None:
        return ""

    return " ".join(
        str(text).strip().lower().split()
    )


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize(
        "NFD",
        str(text),
    )

    result = "".join(
        char
        for char in normalized
        if unicodedata.category(char) != "Mn"
    )

    return (
        result
        .replace("đ", "d")
        .replace("Đ", "D")
    )


def normalized_key(text: str) -> str:
    return remove_accents(
        normalize_text(text)
    )


# ============================================================
# FUZZY MATCH
# ============================================================

def similarity(
    first: str,
    second: str,
) -> float:

    first_key = normalized_key(first)
    second_key = normalized_key(second)

    if not first_key or not second_key:
        return 0.0

    return SequenceMatcher(
        None,
        first_key,
        second_key,
    ).ratio()


def resolve_alias(
    text: str,
) -> str | None:

    value = normalize_text(text)

    if not value:
        return None

    # Exact alias.
    if value in ALIASES:
        return ALIASES[value]

    # Accent-insensitive exact alias.
    value_key = normalized_key(value)

    for alias, canonical in ALIASES.items():

        if normalized_key(alias) == value_key:
            return canonical

    # Fuzzy alias.
    best_target = None
    best_score = 0.0

    for alias, canonical in ALIASES.items():

        alias_key = normalized_key(alias)

        if len(value_key) < 4:
            continue

        if abs(
            len(value_key) - len(alias_key)
        ) > 4:
            continue

        score = similarity(
            value,
            alias,
        )

        if score > best_score:
            best_score = score
            best_target = canonical

    if best_score >= 0.78:
        return best_target

    return None


# ============================================================
# COMMAND CLEANING
# ============================================================

def clean_command(
    text: str,
) -> str:

    command = normalize_text(text)

    if not command:
        return ""

    # Remove common assistant/user prefixes.
    command = re.sub(
        r"^(lam|anh|minh|ánh)\s*[,:\-]?\s*",
        "",
        command,
        flags=re.IGNORECASE,
    )

    return command.strip()


def remove_open_prefix(
    text: str,
) -> str:

    value = clean_command(text)

    prefixes = [
        "mở ",
        "mo ",
        "open ",
        "vào ",
        "vao ",
        "truy cập ",
        "truy cap ",
        "bật ",
        "bat ",
    ]

    for prefix in prefixes:

        if value.startswith(prefix):
            return value[
                len(prefix):
            ].strip()

    return value


# ============================================================
# TARGET DETECTION
# ============================================================

def detect_target(
    text: str,
) -> str | None:

    command = clean_command(text)

    if not command:
        return None

    # Exact target in full command.
    candidates = list(
        ALIASES.keys()
    )

    candidates.sort(
        key=len,
        reverse=True,
    )

    command_key = normalized_key(
        command
    )

    for alias in candidates:

        alias_key = normalized_key(
            alias
        )

        if re.search(
            r"(?<!\w)"
            + re.escape(alias_key)
            + r"(?!\w)",
            command_key,
        ):
            return ALIASES[alias]

    # Try the part after "mở/open/vào".
    target_text = remove_open_prefix(
        command
    )

    resolved = resolve_alias(
        target_text
    )

    if resolved:
        return resolved

    # Last-resort fuzzy full command.
    return resolve_alias(
        command
    )


# ============================================================
# OPEN WINDOWS APPLICATION
# ============================================================

def open_windows_app(
    app_name: str,
) -> tuple[bool, str]:

    target = resolve_alias(
        app_name
    ) or normalize_text(
        app_name
    )

    command = APP_COMMANDS.get(
        target
    )

    if command is None:

        return (
            False,
            f"Ánh chưa có ứng dụng Windows: {app_name}",
        )

    try:

        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return (
            True,
            f"Đã mở {target}.",
        )

    except FileNotFoundError:

        return (
            False,
            f"Không tìm thấy ứng dụng Windows: {target}",
        )

    except Exception as exc:

        return (
            False,
            f"Không thể mở {target}: {exc}",
        )


# ============================================================
# OPEN FOLDER
# ============================================================

def open_folder(
    folder_name: str,
) -> tuple[bool, str]:

    target = resolve_alias(
        folder_name
    ) or normalize_text(
        folder_name
    )

    folder = FOLDERS.get(
        target
    )

    if folder is None:

        return (
            False,
            f"Ánh chưa biết thư mục: {folder_name}",
        )

    try:

        if not folder.exists():

            return (
                False,
                f"Thư mục không tồn tại: {folder}",
            )

        if not hasattr(
            os,
            "startfile",
        ):

            return (
                False,
                "Tính năng mở thư mục chỉ hỗ trợ Windows.",
            )

        os.startfile(
            str(folder)
        )

        return (
            True,
            f"Đã mở {target}.",
        )

    except Exception as exc:

        return (
            False,
            f"Không thể mở thư mục: {exc}",
        )


# ============================================================
# EXPAND SAFE PATH
# ============================================================

def expand_path(
    path_text: str,
) -> Path | None:

    raw = str(
        path_text
    ).strip()

    if not raw:
        return None

    # Remove matching quotes.
    if (
        len(raw) >= 2
        and raw[0] == raw[-1]
        and raw[0] in (
            '"',
            "'",
        )
    ):
        raw = raw[1:-1].strip()

    try:

        path = Path(
            os.path.expandvars(
                os.path.expanduser(
                    raw
                )
            )
        )

        if not path.is_absolute():

            path = (
                Path.cwd()
                / path
            )

        return path.resolve()

    except Exception:
        return None


# ============================================================
# OPEN FILE / PATH
# ============================================================

def open_path(
    path_text: str,
) -> tuple[bool, str]:

    path = expand_path(
        path_text
    )

    if path is None:

        return (
            False,
            "Đường dẫn không hợp lệ.",
        )

    try:

        if not path.exists():

            return (
                False,
                f"Không tìm thấy đường dẫn: {path}",
            )

        if not hasattr(
            os,
            "startfile",
        ):

            return (
                False,
                "Tính năng mở đường dẫn chỉ hỗ trợ Windows.",
            )

        os.startfile(
            str(path)
        )

        if path.is_dir():

            return (
                True,
                f"Đã mở thư mục: {path}",
            )

        return (
            True,
            f"Đã mở file: {path}",
        )

    except Exception as exc:

        return (
            False,
            f"Không thể mở đường dẫn: {exc}",
        )


# ============================================================
# OPEN WEBSITE
# ============================================================

def open_website(
    target: str,
) -> tuple[bool, str]:

    canonical = resolve_alias(
        target
    ) or normalize_text(
        target
    )

    url = WEBSITES.get(
        canonical
    )

    if url is None:

        return (
            False,
            f"Ánh chưa biết website: {target}",
        )

    try:

        opened = webbrowser.open(
            url,
            new=2,
        )

        if not opened:

            return (
                False,
                f"Không thể mở {canonical}.",
            )

        return (
            True,
            f"Đã mở {canonical}.",
        )

    except Exception as exc:

        return (
            False,
            f"Không thể mở {canonical}: {exc}",
        )


# ============================================================
# OPEN URL
# ============================================================

def open_url(
    url: str,
) -> tuple[bool, str]:

    value = str(
        url
    ).strip()

    if not value:

        return (
            False,
            "URL trống.",
        )

    if not (
        value.startswith(
            "http://"
        )
        or value.startswith(
            "https://"
        )
    ):

        value = (
            "https://"
            + value
        )

    try:

        opened = webbrowser.open(
            value,
            new=2,
        )

        if not opened:

            return (
                False,
                "Không thể mở website.",
            )

        return (
            True,
            "Đã mở website.",
        )

    except Exception as exc:

        return (
            False,
            f"Không thể mở website: {exc}",
        )


# ============================================================
# GOOGLE SEARCH
# ============================================================

def search_google(
    query: str,
) -> tuple[bool, str]:

    value = str(
        query
    ).strip()

    if not value:

        return (
            False,
            "Lam chưa nói nội dung cần tìm.",
        )

    url = (
        "https://www.google.com/search?q="
        + quote_plus(value)
    )

    try:

        opened = webbrowser.open(
            url,
            new=2,
        )

        if not opened:

            return (
                False,
                "Không thể mở Google.",
            )

        return (
            True,
            f"Đã mở Google để tìm: {value}",
        )

    except Exception as exc:

        return (
            False,
            f"Không thể mở tìm kiếm: {exc}",
        )


# ============================================================
# SEARCH QUERY EXTRACTION
# ============================================================

def extract_google_query(
    text: str,
) -> str | None:

    command = clean_command(
        text
    )

    prefixes = [
        "tìm trên google ",
        "tim tren google ",
        "tìm google ",
        "tim google ",
        "google tìm ",
        "google tim ",
        "tìm kiếm google ",
        "tim kiem google ",
    ]

    for prefix in prefixes:

        if command.startswith(prefix):

            query = command[
                len(prefix):
            ].strip()

            if query:
                return query

    return None


# ============================================================
# RAW WINDOWS PATH DETECTION
# ============================================================

def looks_like_windows_path(
    text: str,
) -> bool:

    value = str(
        text
    ).strip()

    if not value:
        return False

    return bool(
        re.match(
            r"^(?:[A-Za-z]:[\\/]|\\\\)",
            value,
        )
    )


# ============================================================
# PATH COMMAND
# ============================================================

def extract_path_command(
    text: str,
) -> str | None:

    original = str(
        text
    ).strip()

    command = clean_command(
        original
    )

    prefixes = [
        "mở đường dẫn ",
        "mo duong dan ",
        "mở đường dẫn: ",
        "mo duong dan: ",
        "mở thư mục ",
        "mo thu muc ",
        "mở file ",
        "mo file ",
        "mở tệp ",
        "mo tep ",
    ]

    for prefix in prefixes:

        if command.startswith(prefix):

            # Keep original path characters.
            return original[
                len(prefix):
            ].strip()

    return None


# ============================================================
# SAFE CANONICAL TARGET
# ============================================================

def open_canonical_target(
    target: str,
) -> tuple[bool, str]:

    canonical = resolve_alias(
        target
    )

    if canonical is None:
        canonical = normalize_text(
            target
        )

    if canonical in APP_COMMANDS:

        return open_windows_app(
            canonical
        )

    if canonical in FOLDERS:

        return open_folder(
            canonical
        )

    if canonical in WEBSITES:

        return open_website(
            canonical
        )

    return (
        False,
        "",
    )


# ============================================================
# MAIN EXECUTOR
# ============================================================

def handle_app_command(
    text: str,
) -> tuple[bool, str]:

    original = str(
        text
    ).strip()

    if not original:
        return (
            False,
            "",
        )

    command = clean_command(
        original
    )

    if not command:
        return (
            False,
            "",
        )

    # --------------------------------------------------------
    # DIRECT URL
    # --------------------------------------------------------

    if (
        command.startswith(
            "http://"
        )
        or command.startswith(
            "https://"
        )
        or command.startswith(
            "www."
        )
    ):
        return open_url(
            original
        )

    # --------------------------------------------------------
    # RAW WINDOWS PATH
    # --------------------------------------------------------

    if looks_like_windows_path(
        original
    ):
        return open_path(
            original
        )

    # --------------------------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------------------------

    google_query = extract_google_query(
        command
    )

    if google_query:

        return search_google(
            google_query
        )

    # --------------------------------------------------------
    # PATH COMMAND
    # --------------------------------------------------------

    path_command = extract_path_command(
        original
    )

    if path_command:

        return open_path(
            path_command
        )

    # --------------------------------------------------------
    # TARGET
    # --------------------------------------------------------

    target = detect_target(
        command
    )

    if target:

        # Only execute known safe targets.
        success, response = (
            open_canonical_target(
                target
            )
        )

        if success:
            return (
                True,
                response,
            )

        if response:
            return (
                False,
                response,
            )

    # --------------------------------------------------------
    # "MỞ X" WITH FUZZY TARGET
    # --------------------------------------------------------

    target_text = remove_open_prefix(
        command
    )

    if target_text:

        resolved = resolve_alias(
            target_text
        )

        if resolved:

            return open_canonical_target(
                resolved
            )

    # --------------------------------------------------------
    # STANDALONE TARGET
    # --------------------------------------------------------

    resolved = resolve_alias(
        command
    )

    if resolved:

        return open_canonical_target(
            resolved
        )

    return (
        False,
        "",
    )


# ============================================================
# COMPATIBILITY API
# ============================================================

def execute(
    text: str,
) -> tuple[bool, str]:

    return handle_app_command(
        text
    )


# ============================================================
# STATUS
# ============================================================

def status() -> dict:

    return {
        "module": "App Bridge",
        "role": "executor",
        "applications": len(
            APP_COMMANDS
        ),
        "websites": len(
            WEBSITES
        ),
        "folders": len(
            FOLDERS
        ),
        "aliases": len(
            ALIASES
        ),
        "fuzzy_target": True,
        "natural_commands": True,
        "safe_targets_only": True,
        "ready": True,
    }


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    info = status()

    print()
    print(
        "MINH MINI / ÁNH"
    )
    print(
        "APP BRIDGE — COMPLETE EXECUTOR"
    )
    print()

    print(
        f"Applications : {info['applications']}"
    )

    print(
        f"Websites     : {info['websites']}"
    )

    print(
        f"Folders      : {info['folders']}"
    )

    print(
        f"Aliases      : {info['aliases']}"
    )

    print(
        f"Fuzzy target : {info['fuzzy_target']}"
    )

    print(
        f"Natural cmd  : {info['natural_commands']}"
    )

    print(
        f"Safe targets : {info['safe_targets_only']}"
    )

    print(
        f"Ready        : {info['ready']}"
    )

    print()