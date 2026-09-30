from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re


TARGET_ALIASES = {
    "gg": "google",
    "google": "google",
    "chrome": "google",
    "trình duyệt": "google",
    "youtube": "youtube",
    "yt": "youtube",
    "facebook": "facebook",
    "fb": "facebook",
    "notepad": "notepad",
    "calculator": "calculator",
    "calc": "calculator",
    "máy tính": "calculator",
    "desktop": "desktop",
    "downloads": "downloads",
}


def normalize_text(text: Any) -> str:
    if text is None:
        return ""

    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)

    typo_map = {
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

    low = text.lower()

    for wrong, right in typo_map.items():
        low = low.replace(wrong, right)

    return low


def extract_target(text: str) -> str:
    low = normalize_text(text)

    for alias in sorted(TARGET_ALIASES, key=len, reverse=True):
        if alias in low:
            return TARGET_ALIASES[alias]

    return ""


def extract_action(text: str) -> str:
    low = normalize_text(text)

    if any(x in low for x in [
        "mở", "mo ", "bật", "bat ",
        "khởi động", "chạy"
    ]):
        return "open"

    if any(x in low for x in [
        "đóng", "dong ", "tắt", "tat "
    ]):
        return "close"

    if any(x in low for x in [
        "tìm", "tim ", "tìm kiếm",
        "search", "tra cứu", "tra cuu"
    ]):
        return "search"

    if any(x in low for x in [
        "truy cập", "đi tới",
        "đi đến", "vào "
    ]):
        return "go_to"

    return ""


def extract_topic(text: str) -> str:
    low = normalize_text(text)

    topics = [
        "iphone",
        "samsung",
        "sony",
        "camera",
        "zv-e10",
        "laptop",
        "python",
        "ollama",
        "ai",
        "giun",
        "gà",
        "sâu canxi",
        "phân bò",
        "giá",
        "game",
        "youtube",
        "facebook",
    ]

    for topic in topics:
        if topic in low:
            return topic

    return ""


def extract_query(text: str) -> str:
    value = normalize_text(text)

    for prefix in [
        "tìm kiếm ",
        "tìm ",
        "search ",
        "tra cứu ",
        "tra cuu ",
    ]:
        if value.startswith(prefix):
            return value[len(prefix):].strip()

    return value


def find_reference(text: str) -> str:
    low = normalize_text(text)

    for phrase in [
        "nó",
        "cái này",
        "cái đó",
        "cái kia",
    ]:
        if phrase in low:
            return phrase

    return ""


def detect_intent(
    text: str,
    target: str,
    action: str,
    topic: str,
    reference: str,
    source_number: Optional[int] = None,
) -> str:

    low = normalize_text(text)

    if any(x in low for x in [
        "mấy giờ",
        "bây giờ",
        "giờ hiện tại",
        "giờ rồi",
    ]):
        return "time"

    if (
        "hôm nay" in low
        and not any(x in low for x in [
            "tìm", "giá", "web", "search"
        ])
    ):
        return "date"

    if any(x in low for x in [
        "nhớ ",
        "ghi nhớ",
        "lưu lại",
        "ghi lại",
        "xóa nhớ",
        "memory",
    ]):
        return "memory"

    if any(x in low for x in [
        "tìm trên web",
        "tìm trên mạng",
        "search web",
        "tra cứu trên web",
    ]):
        return "web"

    if action in {"open", "close", "go_to"}:
        return "action"

    if action == "search" and target:
        return "action_web"

    if action == "search" and not target:
        return "web"

    if reference:
        return "follow_up"

    if "?" in text:
        return "question"

    if any(x in low for x in [
        "là gì",
        "bao nhiêu",
        "tại sao",
        "như thế nào",
        "ở đâu",
    ]):
        return "question"

    return "chat"


def choose_tool(
    intent: str,
    target: str,
    action: str,
) -> str:

    if intent in {"time", "date"}:
        return "system_clock"

    if intent == "memory":
        return "memory"

    if intent == "web":
        return "web"

    if intent in {"action", "action_web"}:
        return "execution_controller"

    return "ollama"


def resolve_reference(
    text: str,
    context: Dict[str, Any],
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:

    reference = find_reference(text)

    result = {
        "reference": reference,
        "source_number": None,
        "target": "",
        "topic": "",
        "query": "",
        "action": "",
    }

    low = normalize_text(text)

    needs_context = any(x in low for x in [
        "nó",
        "cái này",
        "cái đó",
        "cái kia",
        "tìm thêm",
        "thêm nữa",
        "rồi sao",
        "vậy sao",
    ])

    # QUAN TRỌNG:
    # Không kế thừa context cho câu độc lập.
    if not needs_context:
        return result

    result["target"] = str(
        context.get("active_target", "")
        or context.get("last_target", "")
        or ""
    )

    result["topic"] = str(
        context.get("active_topic", "")
        or context.get("topic", "")
        or ""
    )

    result["query"] = str(
        context.get("last_query", "")
        or context.get("query", "")
        or ""
    )

    result["action"] = str(
        context.get("active_action", "")
        or context.get("last_action", "")
        or ""
    )

    return result


@dataclass
class BrainDecision:
    original_text: str
    normalized_text: str
    intent: str
    action: str = ""
    tool: str = ""
    target: str = ""
    topic: str = ""
    query: str = ""
    reference: str = ""
    source_number: Optional[int] = None
    is_question: bool = False
    is_action: bool = False
    is_follow_up: bool = False
    needs_context: bool = False
    needs_clarification: bool = False
    confidence: float = 0.0
    reason: str = ""
    missing: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    plan: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BrainCore:

    def __init__(
        self,
        name: str = "MINH MINI BRAIN",
        version: str = "RECOVERY-1",
    ):
        self.name = name
        self.version = version

    def think(
        self,
        message: Any,
        history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> BrainDecision:

        original = "" if message is None else str(message)
        normalized = normalize_text(original)

        ctx = dict(context or {})

        target = extract_target(normalized)
        action = extract_action(normalized)
        topic = extract_topic(normalized)
        query = extract_query(normalized)
        reference = find_reference(normalized)

        resolved = resolve_reference(
            normalized,
            ctx,
            history,
        )

        # Chỉ kế thừa khi thật sự là follow-up.
        if reference:
            target = target or resolved["target"]
            topic = topic or resolved["topic"]
            action = action or resolved["action"]

        intent = detect_intent(
            normalized,
            target,
            action,
            topic,
            reference,
        )

        follow_up = intent == "follow_up"

        tool = choose_tool(
            intent,
            target,
            action,
        )

        missing = []

        if intent == "action" and not target:
            missing.append("target")

        clarification = bool(missing)

        confidence = 0.90

        if clarification:
            confidence = 0.50

        plan = ["respond"]

        if intent in {"action", "action_web"}:
            plan = [
                "execute_action",
                "verify_action",
                "respond",
            ]

        elif intent == "web":
            plan = [
                "search_web",
                "summarize_results",
                "respond",
            ]

        elif intent == "memory":
            plan = [
                "process_memory",
                "respond",
            ]

        return BrainDecision(
            original_text=original,
            normalized_text=normalized,
            intent=intent,
            action=action,
            tool=tool,
            target=target,
            topic=topic,
            query=query,
            reference=reference,
            is_question=("?" in original),
            is_action=intent in {
                "action",
                "action_web",
            },
            is_follow_up=follow_up,
            needs_context=follow_up,
            needs_clarification=clarification,
            confidence=confidence,
            reason=f"intent={intent}",
            missing=missing,
            context=ctx,
            plan=plan,
            metadata={
                "brain": self.name,
                "version": self.version,
            },
        )

    def explain(self, result: BrainDecision) -> str:
        return (
            f"intent={result.intent} | "
            f"action={result.action} | "
            f"target={result.target} | "
            f"topic={result.topic} | "
            f"query={result.query} | "
            f"confidence={result.confidence:.2f}"
        )


BRAIN = BrainCore()


def think(
    message: Any,
    history: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> BrainDecision:

    return BRAIN.think(
        message,
        history=history,
        context=context,
        **kwargs,
    )
