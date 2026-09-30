# ============================================================
# MINH MINI — COMMAND COMPLETION FINAL
# Hoàn thiện câu lệnh trước khi Brain phân tích
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import re


# ============================================================
# RESULT
# ============================================================

@dataclass
class CompletionResult:
    original: str = ""
    completed: str = ""
    changed: bool = False
    confidence: float = 1.0
    reason: str = ""
    intent_hint: str = ""
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)

    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_spaces(text: str) -> str:
    text = clean_text(text)

    text = re.sub(
        r"\s+([,.!?])",
        r"\1",
        text,
    )

    text = re.sub(
        r"([,.!?]){2,}",
        r"\1",
        text,
    )

    return text.strip()


# ============================================================
# TYPOS / ABBREVIATIONS
# ============================================================

WORD_REPLACEMENTS = {
    "m": "mở",
    "mo": "mở",
    "mởg": "mở",
    "dong": "đóng",
    "d": "đóng",
    "tim": "tìm",
    "t": "tìm",
    "yt": "youtube",
    "fb": "facebook",
    "gg": "google",
    "notep": "notepad",
    "notpad": "notepad",
    "calc": "calculator",
    "may tinh": "máy tính",
    "tai xuong": "tải xuống",
    "desktop": "desktop",
}


# ============================================================
# COMMON NATURAL SHORT FORMS
# ============================================================

SHORT_FORMS = {
    "mấy h": "mấy giờ",
    "may h": "mấy giờ",
    "mấy g": "mấy giờ",
    "may g": "mấy giờ",
    "hnay": "hôm nay",
    "hom nay": "hôm nay",
    "hqua": "hôm qua",
    "ngay mai": "ngày mai",
    "ntn": "như thế nào",
    "sao": "thế nào",
    "j": "gì",
    "gì z": "gì",
    "gi z": "gì",
    "gì zậy": "gì vậy",
    "lam oi": "Lam ơi",
    "minh oi": "Minh ơi",
}


# ============================================================
# COMMAND PREFIXES
# ============================================================

COMMAND_PREFIXES = (
    "mở",
    "đóng",
    "tìm",
    "chạy",
    "bật",
    "tắt",
    "vào",
    "đi tới",
    "đi đến",
    "mở giúp",
    "tìm giúp",
    "cho xem",
)


# ============================================================
# TARGET ALIASES
# ============================================================

TARGET_ALIASES = {
    "gg": "Google",
    "google": "Google",
    "gúc": "Google",
    "youtube": "YouTube",
    "yt": "YouTube",
    "facebook": "Facebook",
    "fb": "Facebook",
    "notepad": "Notepad",
    "notep": "Notepad",
    "máy tính": "Calculator",
    "calculator": "Calculator",
    "calc": "Calculator",
    "paint": "Paint",
    "desktop": "Desktop",
    "màn hình chính": "Desktop",
    "tải xuống": "Downloads",
    "downloads": "Downloads",
    "tài liệu": "Documents",
    "documents": "Documents",
    "ảnh": "Pictures",
    "pictures": "Pictures",
    "video": "Videos",
    "videos": "Videos",
    "nhạc": "Music",
    "music": "Music",
}


# ============================================================
# QUESTION WORDS
# ============================================================

QUESTION_STARTS = (
    "gì",
    "sao",
    "tại sao",
    "vì sao",
    "bao nhiêu",
    "bao lâu",
    "khi nào",
    "ở đâu",
    "ai",
    "cái gì",
    "có phải",
    "là gì",
    "thế nào",
    "như thế nào",
)


# ============================================================
# RESULT DETECTION
# ============================================================

def looks_like_question(text: str) -> bool:
    text = clean_text(text).lower()

    if not text:
        return False

    if "?" in text:
        return True

    return any(
        text.startswith(prefix)
        for prefix in QUESTION_STARTS
    )


def looks_like_action(text: str) -> bool:
    text = clean_text(text).lower()

    if not text:
        return False

    return any(
        text.startswith(prefix)
        for prefix in COMMAND_PREFIXES
    )


def looks_like_web_search(text: str) -> bool:
    text = clean_text(text).lower()

    patterns = (
        "tìm trên web",
        "tìm trên mạng",
        "tìm trên google",
        "search web",
        "search google",
        "tra cứu",
        "tìm kiếm",
        "tìm thông tin",
    )

    return any(
        pattern in text
        for pattern in patterns
    )


# ============================================================
# TYPO NORMALIZATION
# ============================================================

def normalize_words(text: str) -> str:
    result = clean_text(text)

    # Cụm dài trước
    for old, new in sorted(
        SHORT_FORMS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        result = re.sub(
            rf"(?<!\w){re.escape(old)}(?!\w)",
            new,
            result,
            flags=re.IGNORECASE,
        )

    # Từ đơn
    words = result.split()

    normalized: list[str] = []

    for word in words:
        stripped = word.strip(".,!?;:")

        replacement = WORD_REPLACEMENTS.get(
            stripped.lower()
        )

        if replacement:
            prefix = word[: len(word) - len(stripped)]
            suffix = word[len(stripped):]

            normalized.append(
                prefix
                + replacement
                + suffix
            )
        else:
            normalized.append(word)

    return normalize_spaces(
        " ".join(normalized)
    )


# ============================================================
# TARGET NORMALIZATION
# ============================================================

def normalize_target(text: str) -> str:
    value = clean_text(text).lower()

    if value in TARGET_ALIASES:
        return TARGET_ALIASES[value]

    return clean_text(text)


# ============================================================
# COMMAND COMPLETION
# ============================================================

def complete_command(
    message: str,
    context: Any = None,
) -> CompletionResult:

    original = clean_text(message)

    if not original:
        return CompletionResult(
            original="",
            completed="",
            changed=False,
            confidence=1.0,
            reason="empty_input",
        )

    text = normalize_words(original)

    # --------------------------------------------------------
    # Remove repeated command words
    # --------------------------------------------------------

    text = re.sub(
        r"^(mở)\s+(mở)\s+",
        r"\1 ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^(tìm)\s+(tìm)\s+",
        r"\1 ",
        text,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # Handle common unfinished commands
    # --------------------------------------------------------

    lower = text.lower()

    if lower in {
        "mở",
        "mo",
    }:
        return CompletionResult(
            original=original,
            completed=text,
            changed=text != original,
            confidence=0.90,
            reason="unfinished_open_command",
            intent_hint="action",
            metadata={
                "needs_target": True,
            },
        )

    if lower in {
        "đóng",
        "dong",
    }:
        return CompletionResult(
            original=original,
            completed=text,
            changed=text != original,
            confidence=0.90,
            reason="unfinished_close_command",
            intent_hint="action",
            metadata={
                "needs_target": True,
            },
        )

    if lower in {
        "tìm",
        "tim",
        "search",
    }:
        return CompletionResult(
            original=original,
            completed=text,
            changed=text != original,
            confidence=0.90,
            reason="unfinished_search_command",
            intent_hint="web",
            metadata={
                "needs_query": True,
            },
        )

    # --------------------------------------------------------
    # Normalize known targets
    # --------------------------------------------------------

    words = text.split()

    if words:
        first = words[0].lower()

        if first in {
            "mở",
            "đóng",
            "tìm",
        } and len(words) >= 2:

            target_text = " ".join(words[1:])
            target = normalize_target(target_text)

            if target != target_text:
                text = (
                    words[0]
                    + " "
                    + target
                )

    # --------------------------------------------------------
    # Natural shorthand
    # --------------------------------------------------------

    if lower == "google":
        text = "mở Google"

    elif lower == "youtube":
        text = "mở YouTube"

    elif lower == "fb":
        text = "mở Facebook"

    elif lower == "facebook":
        text = "mở Facebook"

    elif lower == "notepad":
        text = "mở Notepad"

    elif lower in {
        "calculator",
        "máy tính",
        "calc",
    }:
        text = "mở Calculator"

    # --------------------------------------------------------
    # Web intent hint
    # --------------------------------------------------------

    intent_hint = ""

    if looks_like_web_search(text):
        intent_hint = "web"

    elif looks_like_action(text):
        intent_hint = "action"

    elif looks_like_question(text):
        intent_hint = "question"

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    changed = text != original

    confidence = 1.0

    if changed:
        confidence = 0.96

    if len(text) <= 2:
        confidence = min(
            confidence,
            0.80,
        )

    return CompletionResult(
        original=original,
        completed=text,
        changed=changed,
        confidence=confidence,
        reason=(
            "normalized"
            if changed
            else "already_normalized"
        ),
        intent_hint=intent_hint,
        metadata={
            "question": looks_like_question(text),
            "action": looks_like_action(text),
            "web": looks_like_web_search(text),
        },
    )


# ============================================================
# PUBLIC STRING API
# ============================================================

def normalize_command(
    message: str,
    context: Any = None,
) -> str:

    return complete_command(
        message,
        context=context,
    ).completed


def complete(
    message: str,
    context: Any = None,
) -> str:

    return normalize_command(
        message,
        context=context,
    )


def normalize(
    message: str,
    context: Any = None,
) -> str:

    return normalize_command(
        message,
        context=context,
    )


def process(
    message: str,
    context: Any = None,
) -> CompletionResult:

    return complete_command(
        message,
        context=context,
    )


# ============================================================
# ANALYSIS
# ============================================================

def inspect(
    message: str,
    context: Any = None,
) -> dict[str, Any]:

    result = complete_command(
        message,
        context=context,
    )

    return result.to_dict()


# ============================================================
# DESCRIPTION
# ============================================================

def describe() -> dict[str, Any]:

    return {
        "module": "command_completion",
        "name": "MINH MINI COMMAND COMPLETION FINAL",
        "purpose": (
            "Chuẩn hóa và hoàn thiện input trước "
            "khi Brain phân tích."
        ),
        "features": [
            "typo normalization",
            "abbreviation normalization",
            "unfinished command detection",
            "target normalization",
            "web intent hints",
            "question detection",
            "action detection",
        ],
    }


# ============================================================
# SELF CHECK
# ============================================================

def _self_check() -> dict[str, bool]:

    checks: dict[str, bool] = {}

    # Typo
    r1 = complete_command(
        "mấy h rồi"
    )

    checks["time_typo"] = (
        "mấy giờ" in r1.completed.lower()
    )

    # Google shorthand
    r2 = complete_command(
        "gg"
    )

    checks["google_shortcut"] = (
        r2.completed == "mở Google"
    )

    # YouTube
    r3 = complete_command(
        "youtube"
    )

    checks["youtube_shortcut"] = (
        r3.completed == "mở YouTube"
    )

    # Calculator
    r4 = complete_command(
        "máy tính"
    )

    checks["calculator_shortcut"] = (
        r4.completed == "mở Calculator"
    )

    # Action
    r5 = complete_command(
        "mở gg"
    )

    checks["action_detection"] = (
        r5.intent_hint == "action"
        and r5.completed == "mở Google"
    )

    # Web
    r6 = complete_command(
        "tìm trên web giá iphone"
    )

    checks["web_detection"] = (
        r6.intent_hint == "web"
    )

    # Question
    r7 = complete_command(
        "hôm nay là ngày bao nhiêu?"
    )

    checks["question_detection"] = (
        r7.intent_hint == "question"
    )

    # Empty
    r8 = complete_command("")

    checks["empty_handling"] = (
        r8.completed == ""
    )

    return checks


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "MINH MINI — COMMAND COMPLETION FINAL"
    )

    checks = _self_check()

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