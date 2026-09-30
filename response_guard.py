# ============================================================
# MINH MINI — RESPONSE GUARD FINAL
# Bảo vệ câu trả lời cuối trước khi trả về cho Lam
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import re


# ============================================================
# HELPERS
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)

    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    return text.strip()


def get_value(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(
            name,
            default,
        )

    return getattr(
        obj,
        name,
        default,
    )


def normalize_bool(
    value: Any,
) -> bool:

    if isinstance(value, bool):
        return value

    if value is None:
        return False

    text = clean_text(
        value
    ).lower()

    return text in {
        "true",
        "1",
        "yes",
        "ok",
        "success",
        "successful",
        "thành công",
        "đã thực hiện",
        "đã mở",
        "đã đóng",
    }


# ============================================================
# RESULT
# ============================================================

@dataclass
class ResponseCheck:

    valid: bool = True

    answer: str = ""

    changed: bool = False

    blocked: bool = False

    reason: str = ""

    confidence: float = 1.0

    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# ACTION LANGUAGE
# ============================================================

ACTION_VERBS = (
    "mở",
    "đóng",
    "bật",
    "tắt",
    "chạy",
    "xóa",
    "gửi",
    "đổi",
    "di chuyển",
    "copy",
    "sao chép",
    "dán",
    "tìm",
)


SUCCESS_CLAIMS = (
    "đã mở",
    "đã đóng",
    "đã bật",
    "đã tắt",
    "đã chạy",
    "đã xóa",
    "đã gửi",
    "đã đổi",
    "đã di chuyển",
    "đã sao chép",
    "đã tìm",
    "mình đã",
    "minh đã",
    "đã thực hiện",
    "thực hiện thành công",
    "đã hoàn tất",
)


FAILURE_WORDS = (
    "lỗi",
    "error",
    "failed",
    "failure",
    "không thể",
    "không thực hiện được",
    "thất bại",
    "chưa thực hiện",
    "chưa thể",
    "không có quyền",
    "không tìm thấy",
)


HALLUCINATION_CLAIMS = (
    "đã mở thành công",
    "đã đóng thành công",
    "đã chạy thành công",
    "đã thực hiện thành công",
    "đã hoàn thành thao tác",
)


# ============================================================
# DETECTION
# ============================================================

def is_action_request(
    message: str,
) -> bool:

    text = clean_text(
        message
    ).lower()

    if not text:
        return False

    for verb in ACTION_VERBS:

        if text.startswith(
            verb + " "
        ):
            return True

    return False


def contains_success_claim(
    answer: str,
) -> bool:

    text = clean_text(
        answer
    ).lower()

    return any(
        phrase in text
        for phrase in SUCCESS_CLAIMS
    )


def contains_failure(
    answer: str,
) -> bool:

    text = clean_text(
        answer
    ).lower()

    return any(
        phrase in text
        for phrase in FAILURE_WORDS
    )


def contains_hallucinated_success(
    answer: str,
) -> bool:

    text = clean_text(
        answer
    ).lower()

    return any(
        phrase in text
        for phrase in HALLUCINATION_CLAIMS
    )


# ============================================================
# EXECUTION SUCCESS
# ============================================================

def execution_succeeded(
    execution_result: Any,
) -> bool:

    if execution_result is None:
        return False

    success = get_value(
        execution_result,
        "success",
        None,
    )

    if success is not None:
        return normalize_bool(
            success
        )

    status = clean_text(
        get_value(
            execution_result,
            "status",
            "",
        )
    ).lower()

    if status in {
        "success",
        "successful",
        "ok",
        "done",
        "completed",
        "thành công",
        "hoàn tất",
    }:
        return True

    result = clean_text(
        get_value(
            execution_result,
            "result",
            "",
        )
    ).lower()

    if result in {
        "success",
        "successful",
        "ok",
        "done",
        "completed",
        "thành công",
    }:
        return True

    return False


def execution_failed(
    execution_result: Any,
) -> bool:

    if execution_result is None:
        return False

    success = get_value(
        execution_result,
        "success",
        None,
    )

    if success is False:
        return True

    error = clean_text(
        get_value(
            execution_result,
            "error",
            "",
        )
    )

    return bool(error)


# ============================================================
# INTENT
# ============================================================

def get_intent(
    decision: Any,
) -> str:

    return clean_text(
        get_value(
            decision,
            "intent",
            "",
        )
    ).lower()


def get_tool(
    decision: Any,
) -> str:

    return clean_text(
        get_value(
            decision,
            "tool",
            "",
        )
    ).lower()


def is_real_action(
    decision: Any,
) -> bool:

    intent = get_intent(
        decision
    )

    tool = get_tool(
        decision
    )

    return (
        intent in {
            "action",
            "action_web",
        }
        or tool == "action"
    )


# ============================================================
# RESPONSE CLEANING
# ============================================================

def remove_internal_noise(
    answer: str,
) -> str:

    text = clean_text(
        answer
    )

    if not text:
        return ""

    # Không để model lộ các marker nội bộ
    patterns = (
        r"<\|.*?\|>",
        r"\[INTERNAL\].*?\[/INTERNAL\]",
        r"\[TOOL_RESULT\].*?\[/TOOL_RESULT\]",
    )

    for pattern in patterns:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.DOTALL
            | re.IGNORECASE,
        )

    return clean_text(
        text
    )


def clean_duplicate_prefix(
    answer: str,
) -> str:

    text = clean_text(
        answer
    )

    # Không để kiểu:
    # MINH MINI > MINH MINI > ...
    text = re.sub(
        r"^(?:MINH MINI\s*>\s*)+",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return clean_text(
        text
    )


def clean_empty_lines(
    answer: str,
) -> str:

    lines = [
        line.strip()
        for line in answer.splitlines()
    ]

    cleaned = []

    previous_empty = False

    for line in lines:

        if not line:

            if previous_empty:
                continue

            previous_empty = True
            cleaned.append("")
            continue

        previous_empty = False
        cleaned.append(line)

    return "\n".join(
        cleaned
    ).strip()


def clean_answer(
    answer: str,
) -> str:

    answer = remove_internal_noise(
        answer
    )

    answer = clean_duplicate_prefix(
        answer
    )

    answer = clean_empty_lines(
        answer
    )

    return answer


# ============================================================
# ACTION SAFETY
# ============================================================

def protect_unconfirmed_action(
    message: str,
    answer: str,
    execution_result: Any,
    decision: Any,
) -> tuple[str, bool, str]:

    if not is_action_request(
        message
    ) and not is_real_action(
        decision
    ):
        return (
            answer,
            False,
            "",
        )

    # Có kết quả thành công thật
    if execution_succeeded(
        execution_result
    ):
        return (
            answer,
            False,
            "",
        )

    # Có lỗi thật
    if execution_failed(
        execution_result
    ):
        error = clean_text(
            get_value(
                execution_result,
                "error",
                "",
            )
        )

        if error:
            return (
                "Minh chưa thực hiện được thao tác này: "
                + error,
                True,
                "execution_failed",
            )

        return (
            "Minh chưa thực hiện được thao tác này.",
            True,
            "execution_failed",
        )

    # Nếu câu trả lời tự nhận đã làm nhưng
    # không có execution result thành công
    if contains_success_claim(
        answer
    ):

        return (
            "Minh chưa có xác nhận thực thi thành công "
            "nên không thể nói rằng thao tác đã hoàn tất.",
            True,
            "unconfirmed_action_success",
        )

    return (
        answer,
        False,
        "",
    )


# ============================================================
# OLLAMA CLAIM PROTECTION
# ============================================================

def protect_ollama_action_claim(
    answer: str,
    decision: Any,
    execution_result: Any,
) -> tuple[str, bool, str]:

    tool = get_tool(
        decision
    )

    intent = get_intent(
        decision
    )

    if tool != "ollama" and intent not in {
        "chat",
        "question",
    }:
        return (
            answer,
            False,
            "",
        )

    if execution_succeeded(
        execution_result
    ):
        return (
            answer,
            False,
            "",
        )

    if contains_hallucinated_success(
        answer
    ):

        return (
            "Minh chưa thực hiện thao tác trên máy tính. "
            "Nếu Lam muốn Minh điều khiển máy, Minh cần "
            "chuyển yêu cầu đó qua bộ điều khiển trước.",
            True,
            "ollama_unconfirmed_action_claim",
        )

    return (
        answer,
        False,
        "",
    )


# ============================================================
# SOURCE / URL SAFETY
# ============================================================

def looks_like_fake_source(
    answer: str,
) -> bool:

    text = clean_text(
        answer
    ).lower()

    # Chỉ phát hiện những marker rất rõ,
    # không tự ý xóa URL hợp lệ.
    fake_markers = (
        "[nguồn giả]",
        "[fake source]",
        "nguồn không tồn tại",
        "source không tồn tại",
    )

    return any(
        marker in text
        for marker in fake_markers
    )


def protect_fake_source(
    answer: str,
) -> tuple[str, bool, str]:

    if not looks_like_fake_source(
        answer
    ):
        return (
            answer,
            False,
            "",
        )

    return (
        "Minh không thể xác nhận nguồn được nêu trong "
        "câu trả lời này.",
        True,
        "invalid_source_marker",
    )


# ============================================================
# MAIN VALIDATION
# ============================================================

def validate_response(
    message: str,
    answer: str,
    execution_result: Any = None,
    decision: Any = None,
) -> ResponseCheck:

    original_answer = clean_text(
        answer
    )

    cleaned = clean_answer(
        original_answer
    )

    # --------------------------------------------------------
    # Empty answer
    # --------------------------------------------------------

    if not cleaned:

        return ResponseCheck(
            valid=False,
            answer=(
                "Minh chưa tạo được câu trả lời "
                "cho yêu cầu này."
            ),
            changed=True,
            blocked=False,
            reason="empty_response",
            confidence=1.0,
            metadata={
                "original_empty": True,
            },
        )

    # --------------------------------------------------------
    # Action protection
    # --------------------------------------------------------

    cleaned, changed, reason = (
        protect_unconfirmed_action(
            message,
            cleaned,
            execution_result,
            decision,
        )
    )

    if changed:

        return ResponseCheck(
            valid=True,
            answer=cleaned,
            changed=True,
            blocked=False,
            reason=reason,
            confidence=0.95,
            metadata={
                "action_protected": True,
            },
        )

    # --------------------------------------------------------
    # Ollama protection
    # --------------------------------------------------------

    cleaned, changed, reason = (
        protect_ollama_action_claim(
            cleaned,
            decision,
            execution_result,
        )
    )

    if changed:

        return ResponseCheck(
            valid=True,
            answer=cleaned,
            changed=True,
            blocked=False,
            reason=reason,
            confidence=0.95,
            metadata={
                "ollama_protected": True,
            },
        )

    # --------------------------------------------------------
    # Fake source protection
    # --------------------------------------------------------

    cleaned, changed, reason = (
        protect_fake_source(
            cleaned
        )
    )

    if changed:

        return ResponseCheck(
            valid=True,
            answer=cleaned,
            changed=True,
            blocked=False,
            reason=reason,
            confidence=0.90,
            metadata={
                "source_protected": True,
            },
        )

    # --------------------------------------------------------
    # Normal
    # --------------------------------------------------------

    return ResponseCheck(
        valid=True,
        answer=cleaned,
        changed=(
            cleaned != original_answer
        ),
        blocked=False,
        reason="response_valid",
        confidence=1.0,
        metadata={
            "action_request": is_action_request(
                message
            ),
            "action_intent": is_real_action(
                decision
            ),
            "execution_success": execution_succeeded(
                execution_result
            ),
        },
    )


# ============================================================
# PUBLIC API
# ============================================================

def guard_response(
    message: str,
    answer: str,
    execution_result: Any = None,
    decision: Any = None,
) -> str:

    result = validate_response(
        message,
        answer,
        execution_result=execution_result,
        decision=decision,
    )

    return result.answer


def safe_response(
    message: str,
    answer: str,
    execution_result: Any = None,
    decision: Any = None,
) -> str:

    return guard_response(
        message,
        answer,
        execution_result=execution_result,
        decision=decision,
    )


def check_response(
    message: str,
    answer: str,
    execution_result: Any = None,
    decision: Any = None,
) -> ResponseCheck:

    return validate_response(
        message,
        answer,
        execution_result=execution_result,
        decision=decision,
    )


def inspect_response(
    message: str,
    answer: str,
    execution_result: Any = None,
    decision: Any = None,
) -> dict[str, Any]:

    return check_response(
        message,
        answer,
        execution_result=execution_result,
        decision=decision,
    ).to_dict()


# ============================================================
# DESCRIPTION
# ============================================================

def describe() -> dict[str, Any]:

    return {
        "module": "response_guard",
        "name": "MINH MINI RESPONSE GUARD FINAL",
        "purpose": (
            "Kiểm tra và bảo vệ câu trả lời cuối "
            "trước khi trả cho người dùng."
        ),
        "features": [
            "empty response protection",
            "duplicate prefix cleanup",
            "internal marker cleanup",
            "action success verification",
            "execution failure protection",
            "Ollama action-claim protection",
            "source marker protection",
            "response normalization",
        ],
    }


# ============================================================
# SELF CHECK
# ============================================================

def _self_check() -> dict[str, bool]:

    checks: dict[str, bool] = {}

    # --------------------------------------------------------
    # Normal answer
    # --------------------------------------------------------

    r1 = validate_response(
        "Python là gì?",
        "Python là một ngôn ngữ lập trình.",
        decision={
            "intent": "question",
            "tool": "ollama",
        },
    )

    checks["normal_answer"] = (
        r1.valid
        and "Python" in r1.answer
    )

    # --------------------------------------------------------
    # Empty
    # --------------------------------------------------------

    r2 = validate_response(
        "hello",
        "",
        decision={
            "intent": "chat",
            "tool": "ollama",
        },
    )

    checks["empty_protection"] = (
        r2.valid
        and bool(r2.answer)
    )

    # --------------------------------------------------------
    # Successful action
    # --------------------------------------------------------

    r3 = validate_response(
        "mở Google",
        "Đã mở Google.",
        execution_result={
            "success": True,
        },
        decision={
            "intent": "action",
            "tool": "action",
            "action": "open",
            "target": "Google",
        },
    )

    checks["confirmed_action"] = (
        r3.valid
        and "Google" in r3.answer
    )

    # --------------------------------------------------------
    # Unconfirmed action
    # --------------------------------------------------------

    r4 = validate_response(
        "mở Google",
        "Đã mở Google thành công.",
        execution_result=None,
        decision={
            "intent": "action",
            "tool": "action",
            "action": "open",
            "target": "Google",
        },
    )

    checks["unconfirmed_action"] = (
        r4.valid
        and r4.changed
        and "chưa" in r4.answer.lower()
    )

    # --------------------------------------------------------
    # Failed action
    # --------------------------------------------------------

    r5 = validate_response(
        "mở Google",
        "Đã mở Google.",
        execution_result={
            "success": False,
            "error": "Không tìm thấy trình duyệt.",
        },
        decision={
            "intent": "action",
            "tool": "action",
            "action": "open",
            "target": "Google",
        },
    )

    checks["failed_action"] = (
        r5.valid
        and r5.changed
        and "Không tìm thấy" in r5.answer
    )

    # --------------------------------------------------------
    # Prefix cleanup
    # --------------------------------------------------------

    r6 = validate_response(
        "xin chào",
        "MINH MINI > MINH MINI > Xin chào Lam.",
        decision={
            "intent": "chat",
            "tool": "ollama",
        },
    )

    checks["prefix_cleanup"] = (
        r6.valid
        and r6.answer == "Xin chào Lam."
    )

    return checks


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "MINH MINI — RESPONSE GUARD FINAL"
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