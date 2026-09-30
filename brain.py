from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re


VERSION = "RECOVERY-4"


# ============================================================
# NORMALIZE
# ============================================================

TYPO_MAP = {
    "mấy h": "mấy giờ",
    "may h": "mấy giờ",
    "mấy gio": "mấy giờ",
    "may gio": "mấy giờ",
    "hnay": "hôm nay",
    "hom nayy": "hôm nay",
    "iphonee": "iphone",
    "samsunng": "samsung",
    "youtubee": "youtube",
    "googlle": "google",
    "notepadd": "notepad",
    "calcuator": "calculator",
}


def lower(text: str) -> str:
    return str(text or "").strip().lower()


def normalize_text(text: str) -> str:
    result = str(text or "").strip()

    if not result:
        return ""

    for wrong, correct in sorted(
        TYPO_MAP.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        result = re.sub(
            rf"(?<!\w){re.escape(wrong)}(?!\w)",
            correct,
            result,
            flags=re.IGNORECASE,
        )

    return result.strip()


# ============================================================
# MEMORY
# ============================================================

MEMORY_PATTERNS = (
    "nhớ ",
    "ghi nhớ",
    "lưu lại",
    "lưu ",
    "nhớ rằng",
    "nhớ giúp",
    "hãy nhớ",
)


def is_memory_request(text: str) -> bool:
    low = lower(text)
    return any(pattern in low for pattern in MEMORY_PATTERNS)


# ============================================================
# TARGET
# ============================================================

TARGET_ALIASES = {
    "google": (
        "google",
        "gg",
        "chrome",
        "trình duyệt",
        "trinh duyet",
    ),
    "youtube": (
        "youtube",
        "yt",
    ),
    "facebook": (
        "facebook",
        "fb",
    ),
    "notepad": (
        "notepad++",
        "notepad",
        "sổ ghi chú",
        "so ghi chu",
    ),
    "calculator": (
        "calculator",
        "calc",
        "máy tính",
        "may tinh",
    ),
    "desktop": (
        "desktop",
        "màn hình chính",
        "man hinh chinh",
    ),
    "downloads": (
        "downloads",
        "download",
        "thư mục tải xuống",
        "thu muc tai xuong",
    ),
}


def extract_target(text: str) -> str:
    if is_memory_request(text):
        return ""

    low = lower(text)
    candidates = []

    for target, aliases in TARGET_ALIASES.items():
        for alias in aliases:
            if alias in low:
                candidates.append((len(alias), target))

    if not candidates:
        return ""

    candidates.sort(reverse=True)
    return candidates[0][1]


# ============================================================
# ACTION
# ============================================================

ACTION_ALIASES = {
    "open": (
        "mở",
        "mo",
        "bật",
        "bat",
        "khởi động",
        "khoi dong",
        "chạy",
        "chay",
    ),
    "close": (
        "đóng",
        "dong",
        "tắt",
        "tat",
    ),
    "search": (
        "tìm kiếm",
        "tim kiem",
        "tìm",
        "tim",
        "search",
        "tra cứu",
        "tra cuu",
    ),
    "go_to": (
        "đi tới",
        "di toi",
        "đi đến",
        "di den",
        "truy cập",
        "truy cap",
        "vào",
        "vao",
    ),
}


def extract_action(text: str) -> str:
    if is_memory_request(text):
        return ""

    low = lower(text)
    candidates = []

    for action, aliases in ACTION_ALIASES.items():
        for alias in aliases:
            if alias in low:
                candidates.append((len(alias), action))

    if not candidates:
        return ""

    candidates.sort(reverse=True)
    return candidates[0][1]


# ============================================================
# TOPIC
# ============================================================

# Multi-word topics are checked as phrases.
PHRASE_TOPICS = (
    "giun quế",
    "giun que",
    "sâu canxi",
    "sau canxi",
    "phân bò",
    "phan bo",
    "thời tiết",
    "thoi tiet",
    "chứng khoán",
    "chung khoan",
    "zv-e10",
    "zve10",
)

# Single-word topics are checked as whole words.
WORD_TOPICS = (
    "iphone",
    "samsung",
    "sony",
    "camera",
    "laptop",
    "python",
    "ollama",
    "ai",
    "giun",
    "gà",
    "ga",
    "giá",
    "gia",
    "game",
    "youtube",
    "facebook",
)


def _contains_whole_word(text: str, word: str) -> bool:
    return bool(
        re.search(
            rf"(?<!\w){re.escape(word)}(?!\w)",
            text,
            flags=re.IGNORECASE,
        )
    )


def extract_topic(text: str) -> str:
    low = lower(text)

    if not low:
        return ""

    # Long phrases first.
    for topic in sorted(
        PHRASE_TOPICS,
        key=len,
        reverse=True,
    ):
        if topic in low:
            return topic

    # Then exact standalone words.
    for topic in WORD_TOPICS:
        if _contains_whole_word(low, topic):
            return topic

    return ""


# ============================================================
# QUERY
# ============================================================

def extract_query(text: str) -> str:
    return normalize_text(text)


# ============================================================
# REFERENCE
# ============================================================

def find_reference(text: str) -> str:
    low = lower(text)

    patterns = (
        ("nó", "pronoun:no"),
        ("cái này", "pronoun:this"),
        ("cái đó", "pronoun:that"),
        ("cái kia", "pronoun:that"),
        ("này", "pronoun:this"),
        ("đó", "pronoun:that"),
        ("kia", "pronoun:that"),
    )

    for phrase, reference in patterns:
        if phrase in low:
            return reference

    return ""


def extract_source_number(text: str) -> Optional[int]:
    low = lower(text)

    patterns = (
        r"\bnguồn\s*(\d+)\b",
        r"\bsource\s*(\d+)\b",
        r"\b(?:số|so)\s*(\d+)\b",
        r"\bitem\s*(\d+)\b",
    )

    for pattern in patterns:
        match = re.search(pattern, low)

        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

    return None


def resolve_reference(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:

    context = context or {}

    reference = find_reference(text)
    source_number = extract_source_number(text)

    resolved = {
        "reference": reference,
        "source_number": source_number,
        "target": "",
        "topic": "",
        "query": "",
        "action": "",
    }

    if source_number is not None:
        resolved["reference"] = (
            reference or f"item:{source_number}"
        )

    resolved["target"] = str(
        context.get("active_target")
        or context.get("last_target")
        or ""
    )

    resolved["topic"] = str(
        context.get("active_topic")
        or context.get("topic")
        or ""
    )

    resolved["query"] = str(
        context.get("last_query")
        or context.get("query")
        or ""
    )

    resolved["action"] = str(
        context.get("active_action")
        or context.get("last_action")
        or ""
    )

    low = lower(text)

    if history and any(
        phrase in low
        for phrase in (
            "nó",
            "cái này",
            "cái đó",
            "cái kia",
            "mở nó",
            "đóng nó",
        )
    ):
        for item in reversed(history[-20:]):

            if not isinstance(item, dict):
                continue

            if item.get("role") != "user":
                continue

            content = str(
                item.get("content", "") or ""
            ).strip()

            if not content:
                continue

            previous_target = extract_target(content)
            previous_topic = extract_topic(content)
            previous_action = extract_action(content)
            previous_query = extract_query(content)

            if (
                not resolved["target"]
                and previous_target
            ):
                resolved["target"] = previous_target

            if (
                not resolved["topic"]
                and previous_topic
            ):
                resolved["topic"] = previous_topic

            if (
                not resolved["action"]
                and previous_action
            ):
                resolved["action"] = previous_action

            if (
                not resolved["query"]
                and previous_query
            ):
                resolved["query"] = previous_query

            if (
                resolved["target"]
                or resolved["topic"]
                or resolved["query"]
            ):
                break

    return resolved


# ============================================================
# INTENT
# ============================================================

def is_question(text: str) -> bool:
    low = lower(text)

    if "?" in low:
        return True

    question_phrases = (
        "ai ",
        "ai là",
        "cái gì",
        "cái nào",
        "sao",
        "tại sao",
        "tại sao",
        "vì sao",
        "bao nhiêu",
        "bao lâu",
        "ở đâu",
        "khi nào",
        "thế nào",
        "như thế nào",
        "có phải",
        "phải không",
        "đúng không",
        "là gì",
        "giá bao nhiêu",
    )

    return any(
        phrase in low
        for phrase in question_phrases
    )


def detect_intent(
    text: str,
    target: str = "",
    action: str = "",
    topic: str = "",
    reference: str = "",
    source_number: Optional[int] = None,
) -> str:

    low = lower(text)

    # 1. Memory.
    if is_memory_request(text):
        return "memory"

    # 2. Time.
    if any(
        phrase in low
        for phrase in (
            "mấy giờ",
            "may gio",
            "giờ hiện tại",
            "gio hien tai",
            "bây giờ là mấy giờ",
            "bay gio la may gio",
        )
    ):
        return "time"

    # 3. Date.
    date_phrases = (
        "hôm nay là ngày bao nhiêu",
        "hom nay la ngay bao nhieu",
        "nay là ngày bao nhiêu",
        "nay la ngay bao nhieu",
        "hôm nay ngày mấy",
        "hom nay ngay may",
        "ngày hôm nay",
        "ngay hom nay",
    )

    if any(
        phrase in low
        for phrase in date_phrases
    ):
        return "date"

    # 4. Explicit web.
    if any(
        phrase in low
        for phrase in (
            "tìm trên web",
            "tim tren web",
            "tìm trên mạng",
            "tim tren mang",
            "search web",
            "tìm kiếm trên web",
            "tim kiem tren web",
        )
    ):
        return "web"

    # 5. Action.
    if action or target:

        if action in {
            "open",
            "close",
            "go_to",
        }:
            return "action"

        if (
            action == "search"
            and target in {
                "google",
                "youtube",
                "facebook",
            }
        ):
            return "action_web"

    # 6. Generic search.
    if action == "search":
        return "web"

    # 7. Follow-up.
    if reference:
        return "follow_up"

    if low.startswith(
        (
            "nó",
            "cái này",
            "cái đó",
            "cái kia",
        )
    ):
        return "follow_up"

    # 8. Question.
    if is_question(text):
        return "question"

    return "chat"


# ============================================================
# DECISION
# ============================================================

@dataclass
class BrainDecision:
    text: str
    normalized: str
    intent: str
    action: str = ""
    target: str = ""
    topic: str = ""
    query: str = ""
    reference: str = ""
    source_number: Optional[int] = None
    confidence: float = 0.90
    needs_clarification: bool = False
    missing: List[str] = field(default_factory=list)
    tool: str = ""
    plan: List[str] = field(default_factory=list)
    reason: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# BRAIN CORE
# ============================================================

class BrainCore:

    def __init__(self) -> None:
        self.version = VERSION

    def think(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> BrainDecision:

        history = history or []
        context = dict(context or {})

        original = str(message or "").strip()
        normalized = normalize_text(original)

        if not normalized:
            return BrainDecision(
                text=original,
                normalized="",
                intent="chat",
                confidence=0.20,
                needs_clarification=True,
                missing=["message"],
                reason="empty_input",
                context=context,
                metadata={"version": self.version},
            )

        # Memory gate.
        if is_memory_request(normalized):

            topic = extract_topic(normalized)

            return BrainDecision(
                text=original,
                normalized=normalized,
                intent="memory",
                action="",
                target="",
                topic=topic,
                query=extract_query(normalized),
                reference=find_reference(normalized),
                source_number=extract_source_number(
                    normalized
                ),
                confidence=0.90,
                needs_clarification=False,
                missing=[],
                tool="memory",
                plan=["store_memory"],
                reason="memory_request",
                context={
                    **context,
                    "active_target": "",
                    "active_action": "",
                    "active_topic": topic,
                },
                metadata={
                    "version": self.version,
                    "memory_gate": True,
                },
            )

        # First pass.
        target = extract_target(normalized)
        action = extract_action(normalized)
        topic = extract_topic(normalized)
        query = extract_query(normalized)
        reference = find_reference(normalized)
        source_number = extract_source_number(
            normalized
        )

        # Resolve context.
        resolved = resolve_reference(
            normalized,
            context=context,
            history=history,
        )

        if not target and resolved.get("target"):
            target = str(resolved["target"])

        if not topic and resolved.get("topic"):
            topic = str(resolved["topic"])

        if not action and resolved.get("action"):
            action = str(resolved["action"])

        if (
            not query
            and (
                reference
                or normalized.startswith(
                    (
                        "nó",
                        "cái này",
                        "cái đó",
                        "cái kia",
                    )
                )
            )
        ):
            query = str(
                resolved.get("query")
                or normalized
            )

        if not reference:
            reference = str(
                resolved.get("reference")
                or ""
            )

        if source_number is None:
            source_number = resolved.get(
                "source_number"
            )

        # Intent.
        intent = detect_intent(
            normalized,
            target=target,
            action=action,
            topic=topic,
            reference=reference,
            source_number=source_number,
        )

        if (
            reference
            and intent not in {
                "memory",
                "time",
                "date",
            }
        ):
            intent = "follow_up"

        # Tool.
        tool = ""

        if intent == "memory":
            tool = "memory"
        elif intent in {"web", "action_web"}:
            tool = "web"
        elif intent == "action":
            tool = "action"
        elif intent == "time":
            tool = "system_time"
        elif intent == "date":
            tool = "system_date"

        # Plan.
        if intent == "memory":
            plan = ["store_memory"]
        elif intent == "action":
            plan = ["execute_action"]
        elif intent in {"web", "action_web"}:
            plan = ["search_web", "summarize"]
        elif intent == "time":
            plan = ["get_current_time"]
        elif intent == "date":
            plan = ["get_current_date"]
        elif intent == "follow_up":
            plan = ["resolve_context", "answer"]
        elif intent == "question":
            plan = ["answer_question"]
        else:
            plan = ["chat"]

        # Clarification.
        missing: List[str] = []
        needs_clarification = False

        if intent == "action" and not target:
            needs_clarification = True
            missing.append("target")

        # Confidence.
        confidence = 0.90

        if intent in {"chat", "question"}:
            confidence = 0.75

        if needs_clarification:
            confidence = 0.55

        return BrainDecision(
            text=original,
            normalized=normalized,
            intent=intent,
            action=action,
            target=target,
            topic=topic,
            query=query,
            reference=reference,
            source_number=source_number,
            confidence=confidence,
            needs_clarification=needs_clarification,
            missing=missing,
            tool=tool,
            plan=plan,
            reason=f"detected_{intent}",
            context={
                **context,
                "active_target": target,
                "active_action": action,
                "active_topic": topic,
                "last_query": query,
                "last_reference": reference,
                "last_source_number": source_number,
                "last_intent": intent,
            },
            metadata={
                "version": self.version,
                "memory_gate": False,
            },
        )

    def explain(
        self,
        decision: BrainDecision,
    ) -> str:

        return (
            f"intent={decision.intent} | "
            f"action={decision.action} | "
            f"target={decision.target} | "
            f"topic={decision.topic} | "
            f"query={decision.query} | "
            f"confidence={decision.confidence:.2f}"
        )


# ============================================================
# GLOBAL
# ============================================================

BRAIN = BrainCore()


def think(
    message: str,
    history: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> BrainDecision:

    return BRAIN.think(
        message,
        history=history,
        context=context,
        **kwargs,
    )


__all__ = [
    "VERSION",
    "BrainDecision",
    "BrainCore",
    "BRAIN",
    "think",
    "normalize_text",
    "extract_target",
    "extract_action",
    "extract_topic",
    "extract_query",
    "find_reference",
    "extract_source_number",
    "resolve_reference",
    "detect_intent",
    "is_question",
    "is_memory_request",
]
