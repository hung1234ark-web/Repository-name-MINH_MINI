# ============================================================
# MINH MINI — ROUTER GUARD FINAL
# Kiểm tra và bảo vệ tuyến xử lý trước Execution Controller
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
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_value(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def set_value(
    obj: Any,
    name: str,
    value: Any,
) -> None:

    if obj is None:
        return

    if isinstance(obj, dict):
        obj[name] = value
        return

    try:
        setattr(obj, name, value)
    except Exception:
        pass


# ============================================================
# RESULT
# ============================================================

@dataclass
class RouteCheck:
    valid: bool = True
    intent: str = ""
    tool: str = ""
    action: str = ""
    target: str = ""
    query: str = ""
    needs_clarification: bool = False
    reason: str = ""
    confidence: float = 1.0
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# DETECTION
# ============================================================

QUESTION_WORDS = (
    "gì",
    "sao",
    "tại sao",
    "vì sao",
    "bao nhiêu",
    "bao lâu",
    "khi nào",
    "ở đâu",
    "ai",
    "là gì",
    "thế nào",
    "như thế nào",
    "có phải",
)

ACTION_WORDS = (
    "mở",
    "đóng",
    "chạy",
    "bật",
    "tắt",
    "vào",
    "đi tới",
    "đi đến",
)

WEB_WORDS = (
    "tìm trên web",
    "tìm trên mạng",
    "tìm trên google",
    "tìm trên internet",
    "tra cứu",
    "search web",
    "search google",
    "tìm thông tin",
)


KNOWN_INTENTS = {
    "chat",
    "question",
    "action",
    "action_web",
    "web",
    "web_context",
    "follow_up",
    "time",
    "date",
    "memory",
    "clarification",
}


KNOWN_TOOLS = {
    "chat",
    "ollama",
    "action",
    "web",
    "web_ai",
    "web_context",
    "memory",
    "time",
    "date",
}


INTENT_ALIASES = {
    "conversation": "chat",
    "talk": "chat",
    "qa": "question",
    "ask": "question",
    "command": "action",
    "execute": "action",
    "browser": "web",
    "search": "web",
    "internet": "web",
    "sources": "web_context",
    "context": "web_context",
    "followup": "follow_up",
    "follow-up": "follow_up",
}


TOOL_ALIASES = {
    "llm": "ollama",
    "ai": "ollama",
    "browser": "web",
    "search": "web",
    "action_controller": "action",
    "windows": "action",
    "sources": "web_context",
    "context": "web_context",
}


# ============================================================
# DETECT FUNCTIONS
# ============================================================

def is_question(message: str) -> bool:

    text = clean_text(message).lower()

    if not text:
        return False

    if "?" in text:
        return True

    return any(
        text.startswith(word)
        for word in QUESTION_WORDS
    )


def is_action(message: str) -> bool:

    text = clean_text(message).lower()

    if not text:
        return False

    return any(
        text.startswith(word)
        for word in ACTION_WORDS
    )


def is_web_request(message: str) -> bool:

    text = clean_text(message).lower()

    if not text:
        return False

    return any(
        word in text
        for word in WEB_WORDS
    )


def normalize_intent(intent: Any) -> str:

    value = clean_text(intent).lower()

    if not value:
        return ""

    return INTENT_ALIASES.get(
        value,
        value,
    )


def normalize_tool(tool: Any) -> str:

    value = clean_text(tool).lower()

    if not value:
        return ""

    return TOOL_ALIASES.get(
        value,
        value,
    )


# ============================================================
# ROUTER GUARD
# ============================================================

def validate_route(
    message: str,
    decision: Any = None,
) -> RouteCheck:

    text = clean_text(message)

    intent = normalize_intent(
        get_value(
            decision,
            "intent",
            "",
        )
    )

    tool = normalize_tool(
        get_value(
            decision,
            "tool",
            "",
        )
    )

    action = clean_text(
        get_value(
            decision,
            "action",
            "",
        )
    )

    target = clean_text(
        get_value(
            decision,
            "target",
            "",
        )
    )

    query = clean_text(
        get_value(
            decision,
            "query",
            "",
        )
    )

    reference = clean_text(
        get_value(
            decision,
            "reference",
            "",
        )
    )

    source_number = get_value(
        decision,
        "source_number",
        None,
    )

    is_question_flag = bool(
        get_value(
            decision,
            "is_question",
            False,
        )
    )

    is_action_flag = bool(
        get_value(
            decision,
            "is_action",
            False,
        )
    )

    is_follow_up = bool(
        get_value(
            decision,
            "is_follow_up",
            False,
        )
    )

    needs_clarification = bool(
        get_value(
            decision,
            "needs_clarification",
            False,
        )
    )

    # --------------------------------------------------------
    # Fresh detection
    # --------------------------------------------------------

    detected_question = is_question(text)
    detected_action = is_action(text)
    detected_web = is_web_request(text)

    question = (
        is_question_flag
        or detected_question
    )

    action_request = (
        is_action_flag
        or detected_action
    )

    # --------------------------------------------------------
    # Empty input
    # --------------------------------------------------------

    if not text:

        return RouteCheck(
            valid=False,
            intent="clarification",
            tool="chat",
            needs_clarification=True,
            reason="empty_message",
            confidence=1.0,
        )

    # --------------------------------------------------------
    # Unknown intent
    # --------------------------------------------------------

    if intent and intent not in KNOWN_INTENTS:

        # Nếu message rõ ràng là hành động
        if action_request:
            intent = "action"

        # Nếu rõ ràng là web
        elif detected_web:
            intent = "web"

        # Nếu là câu hỏi
        elif question:
            intent = "question"

        else:
            return RouteCheck(
                valid=False,
                intent="clarification",
                tool="chat",
                target=target,
                query=query,
                needs_clarification=True,
                reason="unknown_intent",
                confidence=0.40,
                metadata={
                    "original_intent": intent,
                },
            )

    # --------------------------------------------------------
    # Missing intent
    # --------------------------------------------------------

    if not intent:

        if detected_web:
            intent = "web"

        elif action_request:
            intent = "action"

        elif question:
            intent = "question"

        elif is_follow_up:
            intent = "follow_up"

        else:
            intent = "chat"

    # --------------------------------------------------------
    # Question override
    #
    # Chỉ override action khi câu thực sự là câu hỏi.
    # --------------------------------------------------------

    if question and not action_request:

        intent = "question"

    # --------------------------------------------------------
    # Clear web request
    # --------------------------------------------------------

    if detected_web and not action_request:

        intent = "web"

    # --------------------------------------------------------
    # Follow-up
    # --------------------------------------------------------

    if is_follow_up:

        intent = "follow_up"

    # --------------------------------------------------------
    # ACTION_WEB
    # --------------------------------------------------------

    if intent == "action_web":

        if query:
            tool = "web"

        elif action and target:
            tool = "action"

        elif target:
            tool = "action"

        else:
            return RouteCheck(
                valid=False,
                intent="clarification",
                tool="chat",
                needs_clarification=True,
                reason="action_web_missing_target_and_query",
                confidence=0.60,
            )

    # --------------------------------------------------------
    # WEB CONTEXT
    # --------------------------------------------------------

    elif intent == "web_context":

        if (
            source_number is not None
            or reference
            or query
            or is_follow_up
        ):
            tool = "web_context"

        else:
            return RouteCheck(
                valid=False,
                intent="clarification",
                tool="chat",
                needs_clarification=True,
                reason="web_context_missing_reference",
                confidence=0.65,
            )

    # --------------------------------------------------------
    # FOLLOW UP
    # --------------------------------------------------------

    elif intent == "follow_up":

        if tool not in KNOWN_TOOLS:
            tool = "chat"

        # Nếu đang có web query/reference
        if (
            query
            or reference
            or source_number is not None
        ):
            tool = (
                "web_context"
                if (
                    reference
                    or source_number is not None
                )
                else "web"
            )

    # --------------------------------------------------------
    # CHAT / QUESTION
    # --------------------------------------------------------

    elif intent in {
        "chat",
        "question",
    }:

        if tool not in KNOWN_TOOLS:
            tool = "ollama"

        if intent == "question":
            tool = (
                "ollama"
                if tool in {
                    "",
                    "chat",
                }
                else tool
            )

    # --------------------------------------------------------
    # ACTION
    # --------------------------------------------------------

    elif intent == "action":

        tool = "action"

        if not action:
            action = "open"

        if not target:

            # Không bắt Brain phải đoán target.
            return RouteCheck(
                valid=False,
                intent="clarification",
                tool="chat",
                action=action,
                target="",
                query=query,
                needs_clarification=True,
                reason="action_missing_target",
                confidence=0.75,
            )

    # --------------------------------------------------------
    # WEB
    # --------------------------------------------------------

    elif intent == "web":

        tool = "web"

        if not query:

            # Nếu message chính nó là truy vấn
            query = text

        if not query:

            return RouteCheck(
                valid=False,
                intent="clarification",
                tool="chat",
                needs_clarification=True,
                reason="web_missing_query",
                confidence=0.75,
            )

    # --------------------------------------------------------
    # TIME / DATE
    # --------------------------------------------------------

    elif intent == "time":

        tool = "time"

    elif intent == "date":

        tool = "date"

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    elif intent == "memory":

        tool = "memory"

    # --------------------------------------------------------
    # CLARIFICATION
    # --------------------------------------------------------

    elif intent == "clarification":

        return RouteCheck(
            valid=False,
            intent="clarification",
            tool="chat",
            action=action,
            target=target,
            query=query,
            needs_clarification=True,
            reason="decision_requests_clarification",
            confidence=1.0,
        )

    # --------------------------------------------------------
    # TOOL VALIDATION
    # --------------------------------------------------------

    if tool and tool not in KNOWN_TOOLS:

        # Repair based on intent
        repair_map = {
            "action": "action",
            "web": "web",
            "web_context": "web_context",
            "question": "ollama",
            "chat": "ollama",
            "memory": "memory",
            "time": "time",
            "date": "date",
            "follow_up": "chat",
        }

        repaired = repair_map.get(intent)

        if repaired:
            tool = repaired

        else:
            return RouteCheck(
                valid=False,
                intent="clarification",
                tool="chat",
                needs_clarification=True,
                reason="unknown_tool",
                confidence=0.50,
                metadata={
                    "original_tool": tool,
                },
            )

    # --------------------------------------------------------
    # Final tool defaults
    # --------------------------------------------------------

    if not tool:

        defaults = {
            "chat": "ollama",
            "question": "ollama",
            "action": "action",
            "web": "web",
            "web_context": "web_context",
            "follow_up": "chat",
            "time": "time",
            "date": "date",
            "memory": "memory",
        }

        tool = defaults.get(
            intent,
            "chat",
        )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence = 0.90

    if intent in {
        "chat",
        "question",
    }:
        confidence = 0.88

    if action_request:
        confidence = max(
            confidence,
            0.92,
        )

    if detected_web:
        confidence = max(
            confidence,
            0.93,
        )

    if needs_clarification:
        confidence = min(
            confidence,
            0.70,
        )

    # --------------------------------------------------------
    # VALID RESULT
    # --------------------------------------------------------

    return RouteCheck(
        valid=not needs_clarification,
        intent=intent,
        tool=tool,
        action=action,
        target=target,
        query=query,
        needs_clarification=needs_clarification,
        reason=(
            "route_valid"
            if not needs_clarification
            else "clarification_required"
        ),
        confidence=confidence,
        metadata={
            "message": text,
            "question": question,
            "action_request": action_request,
            "web_request": detected_web,
            "reference": reference,
            "source_number": source_number,
        },
    )


# ============================================================
# PUBLIC ALIASES
# ============================================================

def guard_route(
    message: str,
    decision: Any = None,
) -> RouteCheck:

    return validate_route(
        message,
        decision,
    )


def check_route(
    message: str,
    decision: Any = None,
) -> RouteCheck:

    return validate_route(
        message,
        decision,
    )


def safe_route(
    message: str,
    decision: Any = None,
) -> RouteCheck:

    return validate_route(
        message,
        decision,
    )


def inspect_route(
    message: str,
    decision: Any = None,
) -> dict[str, Any]:

    return validate_route(
        message,
        decision,
    ).to_dict()


# ============================================================
# DESCRIPTION
# ============================================================

def describe() -> dict[str, Any]:

    return {
        "module": "router_guard",
        "name": "MINH MINI ROUTER GUARD FINAL",
        "purpose": (
            "Kiểm tra tuyến xử lý trước khi "
            "Execution Controller thực thi."
        ),
        "features": [
            "intent validation",
            "tool validation",
            "question protection",
            "action protection",
            "web protection",
            "action_web routing",
            "web context routing",
            "follow-up routing",
            "clarification detection",
        ],
    }


# ============================================================
# SELF CHECK
# ============================================================

def _self_check() -> dict[str, bool]:

    checks: dict[str, bool] = {}

    # --------------------------------------------------------
    # Chat
    # --------------------------------------------------------

    r1 = validate_route(
        "xin chào",
        {
            "intent": "chat",
        },
    )

    checks["chat"] = (
        r1.valid
        and r1.tool == "ollama"
    )

    # --------------------------------------------------------
    # Question
    # --------------------------------------------------------

    r2 = validate_route(
        "Python là gì?",
        {
            "intent": "question",
        },
    )

    checks["question"] = (
        r2.valid
        and r2.tool == "ollama"
    )

    # --------------------------------------------------------
    # Action
    # --------------------------------------------------------

    r3 = validate_route(
        "mở Google",
        {
            "intent": "action",
            "action": "open",
            "target": "Google",
        },
    )

    checks["action"] = (
        r3.valid
        and r3.tool == "action"
        and r3.target == "Google"
    )

    # --------------------------------------------------------
    # Missing target
    # --------------------------------------------------------

    r4 = validate_route(
        "mở",
        {
            "intent": "action",
            "action": "open",
        },
    )

    checks["missing_target"] = (
        r4.needs_clarification
    )

    # --------------------------------------------------------
    # Web
    # --------------------------------------------------------

    r5 = validate_route(
        "tìm trên web giá iPhone",
        {
            "intent": "web",
            "query": "giá iPhone",
        },
    )

    checks["web"] = (
        r5.valid
        and r5.tool == "web"
    )

    # --------------------------------------------------------
    # Web context
    # --------------------------------------------------------

    r6 = validate_route(
        "nguồn 2",
        {
            "intent": "web_context",
            "source_number": 2,
        },
    )

    checks["web_context"] = (
        r6.valid
        and r6.tool == "web_context"
    )

    # --------------------------------------------------------
    # Action web
    # --------------------------------------------------------

    r7 = validate_route(
        "tìm giá iPhone trên web",
        {
            "intent": "action_web",
            "query": "giá iPhone",
            "action": "open",
            "target": "Google",
        },
    )

    checks["action_web"] = (
        r7.valid
        and r7.tool == "web"
    )

    # --------------------------------------------------------
    # Alias
    # --------------------------------------------------------

    r8 = validate_route(
        "xin chào",
        {
            "intent": "conversation",
        },
    )

    checks["intent_alias"] = (
        r8.valid
        and r8.intent == "chat"
    )

    return checks


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "MINH MINI — ROUTER GUARD FINAL"
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