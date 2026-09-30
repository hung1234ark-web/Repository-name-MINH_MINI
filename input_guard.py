# ============================================================
# MINH MINI / ÁNH
# INPUT GUARD — INCOMPLETE / PARTIAL INPUT HANDLER
# ============================================================

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Optional, Tuple


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_spaces(text: str) -> str:
    return " ".join(
        str(text).strip().split()
    )


def remove_accents(text: str) -> str:
    text = unicodedata.normalize(
        "NFD",
        text,
    )

    return "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )


def normalize_key(text: str) -> str:
    return normalize_spaces(
        remove_accents(
            text
        ).lower()
    )


# ============================================================
# COMMON TYPOS
# ============================================================

TYPO_REPLACEMENTS = {
    "iphonee": "iphone",
    "ipone": "iphone",
    "iphon": "iphone",

    "gía": "giá",
    "giaa": "giá",
    "giáa": "giá",
    "gí": "giá",

    "bao nhieu": "bao nhiêu",
    "bao nhiu": "bao nhiêu",

    "tim": "tìm",
    "tim kiem": "tìm kiếm",
    "tra cuu": "tra cứu",

    "may": "mấy",
    "may gio": "mấy giờ",
    "mấy h": "mấy giờ",
    "may h": "mấy giờ",

    "mo": "mở",
    "vao": "vào",

    "hok": "không",
    "ko": "không",

    "dc": "được",
    "duoc": "được",

    "thik": "thích",
    "thich": "thích",

    "nx": "nữa",
    "nua": "nữa",
}


def normalize_typo(text: str) -> str:
    result = normalize_spaces(
        text
    )

    if not result:
        return ""

    ordered = sorted(
        TYPO_REPLACEMENTS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for wrong, correct in ordered:

        result = re.sub(
            r"(?<!\w)"
            + re.escape(wrong)
            + r"(?!\w)",
            correct,
            result,
            flags=re.IGNORECASE,
        )

    return normalize_spaces(
        result
    )


# ============================================================
# PARTIAL / INCOMPLETE COMMANDS
# ============================================================

ACTION_STARTERS = (
    "mở",
    "mo",
    "vào",
    "vao",
    "truy cập",
    "truy cap",
    "chạy",
    "chay",
    "open",
)

WEB_STARTERS = (
    "tìm",
    "tim",
    "tìm kiếm",
    "tim kiem",
    "tra cứu",
    "tra cuu",
    "search",
)

QUESTION_STARTERS = (
    "giá",
    "gia",
    "bao nhiêu",
    "bao nhieu",
    "tại sao",
    "tai sao",
    "vì sao",
    "vi sao",
    "là gì",
    "la gi",
    "thế nào",
    "the nao",
    "ở đâu",
    "o dau",
    "khi nào",
    "khi nao",
)

KNOWN_TARGETS = {
    "google",
    "gg",
    "youtube",
    "yt",
    "facebook",
    "fb",
    "chrome",
    "notepad",
    "calculator",
    "calc",
    "paint",
    "explorer",
    "desktop",
    "download",
    "downloads",
    "documents",
    "pictures",
    "videos",
    "music",
}


# ============================================================
# DETECTION
# ============================================================

def starts_with_any(
    key: str,
    values: tuple[str, ...],
) -> bool:

    for value in values:

        value_key = normalize_key(
            value
        )

        if (
            key == value_key
            or key.startswith(
                value_key + " "
            )
        ):
            return True

    return False


def detect_input_state(
    text: str,
) -> Dict[str, Any]:

    original = normalize_spaces(
        text
    )

    normalized = normalize_typo(
        original
    )

    key = normalize_key(
        normalized
    )

    result = {
        "original": original,
        "normalized": normalized,
        "empty": not bool(
            normalized
        ),
        "partial": False,
        "action_partial": False,
        "web_partial": False,
        "question_partial": False,
        "needs_continuation": False,
        "target": "",
    }

    if not normalized:
        return result

    words = key.split()

    # --------------------------------------------------------
    # Câu cực ngắn có khả năng là câu cụt.
    # --------------------------------------------------------

    if len(words) <= 3:

        if starts_with_any(
            key,
            ACTION_STARTERS,
        ):

            result["partial"] = True
            result["action_partial"] = True
            result["needs_continuation"] = True

        elif starts_with_any(
            key,
            WEB_STARTERS,
        ):

            result["partial"] = True
            result["web_partial"] = True
            result["needs_continuation"] = True

        elif starts_with_any(
            key,
            QUESTION_STARTERS,
        ):

            result["partial"] = True
            result["question_partial"] = True
            result["needs_continuation"] = True

    # --------------------------------------------------------
    # Nhận diện target dù câu chưa hoàn chỉnh.
    # --------------------------------------------------------

    for target in KNOWN_TARGETS:

        target_key = normalize_key(
            target
        )

        if (
            key == target_key
            or f" {target_key} " in f" {key} "
        ):

            result["target"] = target
            break

    # --------------------------------------------------------
    # Nếu có động từ + chưa có target,
    # coi là action thiếu đối tượng.
    # --------------------------------------------------------

    if (
        starts_with_any(
            key,
            ACTION_STARTERS,
        )
        and not result["target"]
    ):

        result["partial"] = True
        result["action_partial"] = True
        result["needs_continuation"] = True

    # --------------------------------------------------------
    # Tìm query kiểu:
    # "tìm iphone"
    # "mở"
    # "tìm giá"
    # --------------------------------------------------------

    if (
        starts_with_any(
            key,
            WEB_STARTERS,
        )
        and len(words) <= 2
    ):

        result["partial"] = True
        result["web_partial"] = True
        result["needs_continuation"] = True

    return result


# ============================================================
# REPAIR / CONTINUATION
# ============================================================

def repair_partial_input(
    text: str,
    history: Optional[
        list[dict[str, str]]
    ] = None,
) -> Tuple[str, Dict[str, Any]]:

    original = normalize_spaces(
        text
    )

    normalized = normalize_typo(
        original
    )

    state = detect_input_state(
        normalized
    )

    if not state["needs_continuation"]:
        return normalized, state

    if not history:
        return normalized, state

    last_user = ""

    for item in reversed(
        history
    ):

        if not isinstance(
            item,
            dict,
        ):
            continue

        if item.get(
            "role"
        ) != "user":
            continue

        content = normalize_spaces(
            item.get(
                "content",
                "",
            )
        )

        if content:
            last_user = content
            break

    if not last_user:
        return normalized, state

    last_key = normalize_key(
        last_user
    )

    current_key = normalize_key(
        normalized
    )

    # --------------------------------------------------------
    # "giá" sau "iphone 17"
    # --------------------------------------------------------

    if (
        state["question_partial"]
        and current_key in {
            "gia",
            "bao nhieu",
            "the nao",
            "sao",
        }
    ):

        repaired = (
            f"{last_user} "
            f"{normalized}"
        )

        state["repaired_from"] = last_user

        return normalize_spaces(
            repaired
        ), state

    # --------------------------------------------------------
    # "mở" sau "youtube"
    # --------------------------------------------------------

    if (
        state["action_partial"]
        and current_key in {
            "mo",
            "vao",
            "truy cap",
            "open",
        }
    ):

        repaired = (
            f"{normalized} "
            f"{last_user}"
        )

        state["repaired_from"] = last_user

        return normalize_spaces(
            repaired
        ), state

    # --------------------------------------------------------
    # "tìm" sau chủ đề vừa nói
    # --------------------------------------------------------

    if (
        state["web_partial"]
        and current_key in {
            "tim",
            "tìm",
            "search",
            "tra cuu",
            "tra cứu",
        }
    ):

        repaired = (
            f"{normalized} "
            f"{last_user}"
        )

        state["repaired_from"] = last_user

        return normalize_spaces(
            repaired
        ), state

    return normalized, state


# ============================================================
# SAFE INPUT
# ============================================================

def safe_input(
    value: Any,
) -> str:

    if value is None:
        return ""

    try:
        text = str(value)

    except Exception:
        return ""

    text = text.replace(
        "\x00",
        "",
    )

    return normalize_spaces(
        text
    )


# ============================================================
# PUBLIC API
# ============================================================

def analyze_input(
    text: Any,
    history: Optional[
        list[dict[str, str]]
    ] = None,
) -> Dict[str, Any]:

    safe_text = safe_input(
        text
    )

    repaired, state = repair_partial_input(
        safe_text,
        history,
    )

    state["safe_text"] = safe_text
    state["repaired_text"] = repaired

    return state


def prepare_input(
    text: Any,
    history: Optional[
        list[dict[str, str]]
    ] = None,
) -> str:

    result = analyze_input(
        text,
        history,
    )

    return str(
        result.get(
            "repaired_text",
            "",
        )
    )


# ============================================================
# SELF CHECK
# ============================================================

if __name__ == "__main__":

    fake_history = [
        {
            "role": "user",
            "content": "iphone 17",
        },
        {
            "role": "assistant",
            "content": "Được.",
        },
    ]

    tests = [
        "",
        "mở",
        "tìm",
        "giá",
        "mấy h",
        "iphonee",
        "mở youtube",
    ]

    for item in tests:

        print()
        print(
            "=" * 60
        )

        print(
            "INPUT:",
            repr(item),
        )

        print(
            "RESULT:"
        )

        print(
            analyze_input(
                item,
                fake_history,
            )
        )