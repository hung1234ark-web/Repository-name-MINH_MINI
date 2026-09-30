# ============================================================
# MINH MINI — CONTEXT MANAGER FINAL
# ------------------------------------------------------------
# Nhiệm vụ:
#   - Giữ mạch hội thoại hiện tại
#   - Biết Lam đang nói về chủ đề nào
#   - Biết đối tượng nào đang được nhắc tới
#   - Nhớ hành động gần nhất
#   - Nhớ câu hỏi / truy vấn gần nhất
#   - Nhớ kết quả gần nhất
#   - Nhớ nguồn đang được chọn
#   - Hiểu tham chiếu:
#         nó
#         cái này
#         cái kia
#         cái trước
#         cái 2
#         nguồn 2
#         tìm thêm
#         mở nó
#         còn cái kia?
#
# Module này KHÔNG thực thi hành động.
# Nó chỉ quản lý ngữ cảnh để Brain dùng.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import re


# ============================================================
# CONSTANTS
# ============================================================

MAX_HISTORY = 40
MAX_CONTEXT_SCAN = 20


# ============================================================
# NORMALIZE
# ============================================================

def normalize_text(text: Any) -> str:
    if text is None:
        return ""

    text = str(text)

    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "\u00a0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text).strip()

    return text


def lower(text: Any) -> str:
    return normalize_text(text).lower()


# ============================================================
# HISTORY VALIDATION
# ============================================================

def validate_history(
    history: Any,
) -> List[Dict[str, str]]:

    if not isinstance(history, list):
        return []

    result: List[Dict[str, str]] = []

    for item in history[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue

        role = str(item.get("role", "")).strip().lower()
        content = normalize_text(item.get("content", ""))

        if role not in {"user", "assistant", "system"}:
            continue

        if not content:
            continue

        result.append({
            "role": role,
            "content": content,
        })

    return result


# ============================================================
# BASIC HISTORY HELPERS
# ============================================================

def recent_messages(
    history: Any,
    limit: int = 10,
) -> List[Dict[str, str]]:

    valid = validate_history(history)

    if limit <= 0:
        return []

    return valid[-limit:]


def last_user(
    history: Any,
) -> str:

    valid = validate_history(history)

    for item in reversed(valid):
        if item["role"] == "user":
            return item["content"]

    return ""


def previous_user(
    history: Any,
    skip: int = 1,
) -> str:

    valid = validate_history(history)

    count = 0

    for item in reversed(valid):
        if item["role"] != "user":
            continue

        if count == skip:
            return item["content"]

        count += 1

    return ""


def last_assistant(
    history: Any,
) -> str:

    valid = validate_history(history)

    for item in reversed(valid):
        if item["role"] == "assistant":
            return item["content"]

    return ""


# ============================================================
# SHORT REPLIES
# ============================================================

SHORT_REPLIES = {
    "có",
    "không",
    "ko",
    "không cần",
    "được",
    "ok",
    "oke",
    "okay",
    "ừ",
    "ờ",
    "uh",
    "đúng",
    "sai",
    "rồi",
    "chưa",
    "tiếp",
    "làm đi",
    "làm",
    "thêm",
}


def is_short_reply(
    text: Any,
) -> bool:

    low = lower(text)

    if not low:
        return False

    if low in SHORT_REPLIES:
        return True

    if re.fullmatch(r"\d+", low):
        return True

    return len(low) <= 8


# ============================================================
# REFERENCE DETECTION
# ============================================================

REFERENCE_PATTERNS = [
    "nó",
    "cái này",
    "cái đó",
    "cái kia",
    "cái trước",
    "cái sau",
    "cái trên",
    "cái dưới",
    "thứ này",
    "thứ đó",
    "thứ kia",
    "phần này",
    "phần đó",
    "nguồn này",
    "nguồn đó",
    "nguồn trước",
    "nguồn sau",
    "kết quả này",
    "kết quả đó",
    "việc này",
    "việc đó",
    "vấn đề này",
    "vấn đề đó",
    "tìm thêm",
    "thêm nữa",
    "còn cái kia",
    "còn cái đó",
    "còn cái này",
    "mở nó",
    "đóng nó",
    "xem nó",
]


def has_reference(
    text: Any,
) -> bool:

    low = lower(text)

    if not low:
        return False

    if re.search(r"\b(?:nguồn|source)\s*\d+\b", low):
        return True

    if re.search(r"\b(?:cái|thứ)\s*\d+\b", low):
        return True

    if re.fullmatch(r"\d+", low):
        return True

    return any(
        pattern in low
        for pattern in REFERENCE_PATTERNS
    )


def extract_reference(
    text: Any,
) -> str:

    low = lower(text)

    if not low:
        return ""

    match = re.search(
        r"\b(?:nguồn|source)\s*(\d+)\b",
        low,
    )

    if match:
        return f"source:{match.group(1)}"

    match = re.search(
        r"\b(?:cái|thứ)\s*(\d+)\b",
        low,
    )

    if match:
        return f"item:{match.group(1)}"

    if re.fullmatch(r"\d+", low):
        return f"item:{int(low)}"

    for pattern in REFERENCE_PATTERNS:
        if pattern in low:
            return pattern

    return ""


def extract_source_number(
    text: Any,
) -> Optional[int]:

    low = lower(text)

    match = re.search(
        r"\b(?:nguồn|source)\s*(\d+)\b",
        low,
    )

    if match:
        return int(match.group(1))

    match = re.search(
        r"\b(?:cái|thứ)\s*(\d+)\b",
        low,
    )

    if match:
        return int(match.group(1))

    if re.fullmatch(r"\d+", low):
        return int(low)

    return None


# ============================================================
# SIMPLE EXTRACTION
# ============================================================

TARGET_ALIASES = {
    "google": [
        "google",
        "chrome",
        "trình duyệt",
    ],
    "youtube": [
        "youtube",
        "yt",
    ],
    "facebook": [
        "facebook",
        "fb",
    ],
    "notepad": [
        "notepad",
        "sổ ghi chú",
    ],
    "calculator": [
        "calculator",
        "calc",
        "máy tính",
    ],
    "paint": [
        "paint",
    ],
    "explorer": [
        "explorer",
        "file explorer",
        "quản lý tệp",
    ],
    "desktop": [
        "desktop",
        "màn hình desktop",
        "màn hình chính",
    ],
    "downloads": [
        "downloads",
        "download",
        "thư mục tải xuống",
    ],
    "documents": [
        "documents",
        "document",
        "tài liệu",
    ],
    "pictures": [
        "pictures",
        "ảnh",
    ],
    "videos": [
        "videos",
        "video",
    ],
    "music": [
        "music",
        "nhạc",
    ],
    "this_pc": [
        "this pc",
        "máy tính này",
        "computer",
    ],
}


def extract_target(
    text: Any,
) -> str:

    low = lower(text)

    for target, aliases in TARGET_ALIASES.items():
        for alias in sorted(
            aliases,
            key=len,
            reverse=True,
        ):
            if alias in low:
                return target

    return ""


ACTION_WORDS = {
    "open": [
        "mở",
        "bật",
        "khởi động",
        "chạy",
    ],
    "close": [
        "đóng",
        "tắt",
    ],
    "search": [
        "tìm",
        "tìm kiếm",
        "search",
        "tra cứu",
    ],
}


def extract_action(
    text: Any,
) -> str:

    low = lower(text)

    for action, words in ACTION_WORDS.items():
        for word in words:
            if word in low:
                return action

    return ""


# ============================================================
# TOPIC / QUERY
# ============================================================

TOPIC_HINTS = [
    "iphone",
    "samsung",
    "sony",
    "zv-e10",
    "camera",
    "laptop",
    "python",
    "ollama",
    "ai",
    "minh mini",
    "giun",
    "gà",
    "sâu canxi",
    "phân bò",
    "giá",
    "thời tiết",
    "chứng khoán",
    "game",
]


def extract_topic(
    text: Any,
) -> str:

    low = lower(text)

    for topic in TOPIC_HINTS:
        if topic in low:
            return topic

    return ""


def extract_query(
    text: Any,
) -> str:

    value = normalize_text(text)

    if not value:
        return ""

    value = re.sub(
        r"^(mở|bật|đóng|tắt|tìm|tìm kiếm|search|tra cứu)\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )

    return value.rstrip(" ?").strip()


# ============================================================
# CONTEXT STATE
# ============================================================

@dataclass
class ConversationState:
    active_topic: str = ""
    active_target: str = ""
    active_object: str = ""
    active_action: str = ""

    last_intent: str = ""
    last_query: str = ""
    last_user_message: str = ""
    last_assistant_message: str = ""

    last_result: str = ""

    active_reference: str = ""
    last_reference: str = ""

    active_source_number: Optional[int] = None
    last_source_number: Optional[int] = None

    pending_clarification: bool = False
    pending_action: str = ""

    turn_count: int = 0

    extra: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# STATE FROM HISTORY
# ============================================================

def _scan_history(
    history: List[Dict[str, str]],
) -> ConversationState:

    state = ConversationState()

    state.turn_count = len(
        [
            item
            for item in history
            if item.get("role") == "user"
        ]
    )

    for item in reversed(history[-MAX_CONTEXT_SCAN:]):

        role = item.get("role", "")
        content = normalize_text(
            item.get("content", "")
        )

        if not content:
            continue

        if role == "assistant":

            if not state.last_assistant_message:
                state.last_assistant_message = content

                # giữ toàn bộ câu trả lời gần nhất
                # làm last result nếu chưa có
                if not state.last_result:
                    state.last_result = content

            continue

        if role != "user":
            continue

        if not state.last_user_message:
            state.last_user_message = content

        target = extract_target(content)
        action = extract_action(content)
        topic = extract_topic(content)
        query = extract_query(content)
        reference = extract_reference(content)
        source_number = extract_source_number(content)

        if not state.active_target and target:
            state.active_target = target

        if not state.active_object and target:
            state.active_object = target

        if not state.active_action and action:
            state.active_action = action

        if not state.active_topic and topic:
            state.active_topic = topic

        if not state.last_query and query:
            state.last_query = query

        if not state.last_reference and reference:
            state.last_reference = reference

        if not state.active_reference and reference:
            state.active_reference = reference

        if state.last_source_number is None:
            if source_number is not None:
                state.last_source_number = source_number

        if state.active_source_number is None:
            if source_number is not None:
                state.active_source_number = source_number

        break

    return state


def build_state(
    history: Any,
    current_topic: str = "",
    current_query: str = "",
    current_target: str = "",
    current_action: str = "",
    **kwargs,
) -> ConversationState:

    valid = validate_history(history)

    state = _scan_history(valid)

    if current_topic:
        state.active_topic = normalize_text(
            current_topic
        )

    if current_query:
        state.last_query = normalize_text(
            current_query
        )

    if current_target:
        state.active_target = normalize_text(
            current_target
        )
        state.active_object = normalize_text(
            current_target
        )

    if current_action:
        state.active_action = normalize_text(
            current_action
        )

    # hỗ trợ Brain / router truyền thêm dữ liệu
    for key in [
        "last_intent",
        "last_result",
        "pending_action",
        "pending_clarification",
    ]:
        if key in kwargs and kwargs[key] not in (
            None,
            "",
        ):
            setattr(
                state,
                key,
                kwargs[key],
            )

    return state


# ============================================================
# MERGE
# ============================================================

def merge_state(
    old_state: Any,
    new_state: Any,
) -> ConversationState:

    if isinstance(old_state, ConversationState):
        result = ConversationState(
            **old_state.to_dict()
        )
    else:
        result = ConversationState()

    if isinstance(new_state, ConversationState):
        data = new_state.to_dict()
    elif isinstance(new_state, dict):
        data = dict(new_state)
    else:
        data = {}

    for key, value in data.items():

        if key == "extra":
            if isinstance(value, dict):
                result.extra.update(value)

            continue

        if value in (
            "",
            None,
            False,
        ):
            continue

        try:
            setattr(
                result,
                key,
                value,
            )
        except Exception:
            pass

    return result


def get_state(
    history: Any,
    **kwargs,
) -> Dict[str, Any]:

    return build_state(
        history,
        **kwargs,
    ).to_dict()


# ============================================================
# UPDATE STATE AFTER A TURN
# ============================================================

def update_state(
    previous_state: Any,
    message: str = "",
    role: str = "user",
    decision: Any = None,
    result: Any = None,
) -> ConversationState:

    if isinstance(previous_state, ConversationState):
        state = ConversationState(
            **previous_state.to_dict()
        )
    elif isinstance(previous_state, dict):
        state = ConversationState(
            **{
                key: value
                for key, value in previous_state.items()
                if key in ConversationState.__dataclass_fields__
            }
        )
    else:
        state = ConversationState()

    text = normalize_text(message)

    if role == "user":

        if text:
            state.last_user_message = text

        target = extract_target(text)
        action = extract_action(text)
        topic = extract_topic(text)
        query = extract_query(text)
        reference = extract_reference(text)
        source_number = extract_source_number(text)

        if target:
            state.active_target = target
            state.active_object = target

        if action:
            state.active_action = action

        if topic:
            state.active_topic = topic

        if query and not has_reference(text):
            state.last_query = query

        if reference:
            state.active_reference = reference
            state.last_reference = reference

        if source_number is not None:
            state.active_source_number = source_number
            state.last_source_number = source_number

        state.turn_count += 1

    elif role == "assistant":

        if text:
            state.last_assistant_message = text
            state.last_result = text

    # --------------------------------------------------------
    # decision integration
    # --------------------------------------------------------

    if decision is not None:

        if hasattr(decision, "to_dict"):
            data = decision.to_dict()
        elif isinstance(decision, dict):
            data = decision
        else:
            data = {}

        if data:

            if data.get("intent"):
                state.last_intent = data["intent"]

            if data.get("target"):
                state.active_target = data["target"]
                state.active_object = data["target"]

            if data.get("action"):
                state.active_action = data["action"]

            if data.get("topic"):
                state.active_topic = data["topic"]

            if data.get("query"):
                state.last_query = data["query"]

            if data.get("reference"):
                state.active_reference = data["reference"]
                state.last_reference = data["reference"]

            if data.get("source_number") is not None:
                state.active_source_number = data["source_number"]
                state.last_source_number = data[
                    "source_number"
                ]

            state.pending_clarification = bool(
                data.get(
                    "needs_clarification",
                    False,
                )
            )

            if state.pending_clarification:
                state.pending_action = (
                    data.get("action")
                    or state.active_action
                    or ""
                )

    # --------------------------------------------------------
    # result integration
    # --------------------------------------------------------

    if result is not None:

        if isinstance(result, str):
            state.last_result = result

        elif isinstance(result, dict):
            value = (
                result.get("result")
                or result.get("response")
                or result.get("message")
                or result.get("text")
            )

            if value:
                state.last_result = str(value)

    return state


# ============================================================
# CONTEXT DECISION
# ============================================================

def should_use_previous_context(
    text: Any,
    state: Any = None,
) -> bool:

    value = normalize_text(text)

    if not value:
        return False

    if has_reference(value):
        return True

    if is_short_reply(value):
        return state is not None

    low = value.lower()

    patterns = [
        "còn",
        "vậy",
        "thế",
        "rồi sao",
        "tìm thêm",
        "thêm nữa",
        "mở nó",
        "đóng nó",
        "xem nó",
        "cái kia",
        "cái đó",
        "cái này",
        "nguồn trước",
        "nguồn sau",
    ]

    return any(
        pattern in low
        for pattern in patterns
    )


# ============================================================
# RESOLVE REFERENCE
# ============================================================

def _state_to_dict(
    state: Any,
) -> Dict[str, Any]:

    if isinstance(state, ConversationState):
        return state.to_dict()

    if isinstance(state, dict):
        return dict(state)

    return {}


def resolve_best_context(
    text: str,
    history: Any = None,
    state: Any = None,
) -> Dict[str, Any]:

    # tương thích với cách gọi cũ:
    # resolve_best_context(history)
    if isinstance(text, list) and history is None:
        history = text
        text = ""

    valid_history = validate_history(
        history or []
    )

    if state is None:
        state_obj = _scan_history(valid_history)
    else:
        state_obj = (
            state
            if isinstance(state, ConversationState)
            else ConversationState(**{
                key: value
                for key, value in _state_to_dict(state).items()
                if key in ConversationState.__dataclass_fields__
            })
        )

    state_data = _state_to_dict(state_obj)

    value = normalize_text(text)
    low = lower(value)

    reference = extract_reference(value)
    source_number = extract_source_number(value)

    resolved = {
        "reference": reference,
        "source_number": source_number,

        "topic": state_data.get(
            "active_topic",
            "",
        ),

        "target": state_data.get(
            "active_target",
            "",
        ),

        "object": state_data.get(
            "active_object",
            "",
        ),

        "action": state_data.get(
            "active_action",
            "",
        ),

        "query": state_data.get(
            "last_query",
            "",
        ),

        "intent": state_data.get(
            "last_intent",
            "",
        ),

        "result": state_data.get(
            "last_result",
            "",
        ),

        "pending_action": state_data.get(
            "pending_action",
            "",
        ),
    }

    # --------------------------------------------------------
    # explicit number
    # --------------------------------------------------------

    if source_number is not None:

        resolved["reference"] = (
            reference
            or f"item:{source_number}"
        )

        resolved["source_number"] = (
            source_number
        )

    # --------------------------------------------------------
    # "nó / cái này / cái đó / cái kia"
    # --------------------------------------------------------

    pronoun_reference = any(
        phrase in low
        for phrase in [
            "nó",
            "cái này",
            "cái đó",
            "cái kia",
            "mở nó",
            "đóng nó",
            "xem nó",
        ]
    )

    if pronoun_reference:

        # ưu tiên target hiện tại
        if not resolved["target"]:
            resolved["target"] = (
                state_data.get(
                    "active_target",
                    "",
                )
            )

        if not resolved["object"]:
            resolved["object"] = (
                state_data.get(
                    "active_object",
                    "",
                )
            )

        # fallback về user message gần nhất
        if valid_history:

            for item in reversed(
                valid_history
            ):

                if item["role"] != "user":
                    continue

                previous_target = extract_target(
                    item["content"]
                )

                previous_topic = extract_topic(
                    item["content"]
                )

                previous_action = extract_action(
                    item["content"]
                )

                if previous_target and not resolved["target"]:
                    resolved["target"] = (
                        previous_target
                    )

                if previous_topic and not resolved["topic"]:
                    resolved["topic"] = (
                        previous_topic
                    )

                if previous_action and not resolved["action"]:
                    resolved["action"] = (
                        previous_action
                    )

                if (
                    resolved["target"]
                    or resolved["topic"]
                    or resolved["action"]
                ):
                    break

    # --------------------------------------------------------
    # "tìm thêm" / "còn cái kia"
    # --------------------------------------------------------

    continue_patterns = [
        "tìm thêm",
        "thêm nữa",
        "còn cái kia",
        "còn cái đó",
        "còn cái này",
        "rồi sao",
        "vậy sao",
        "thế sao",
    ]

    if any(
        pattern in low
        for pattern in continue_patterns
    ):

        if not resolved["query"]:
            resolved["query"] = (
                state_data.get(
                    "last_query",
                    "",
                )
            )

        if not resolved["topic"]:
            resolved["topic"] = (
                state_data.get(
                    "active_topic",
                    "",
                )
            )

    # --------------------------------------------------------
    # action follow-up
    # --------------------------------------------------------

    if low.startswith("mở") and (
        "nó" in low
        or "cái này" in low
        or "cái đó" in low
        or "cái kia" in low
    ):

        resolved["action"] = "open"

    elif low.startswith("đóng") and (
        "nó" in low
        or "cái này" in low
        or "cái đó" in low
        or "cái kia" in low
    ):

        resolved["action"] = "close"

    # --------------------------------------------------------
    # preserve pending action
    # --------------------------------------------------------

    if state_data.get("pending_action"):
        if not resolved["action"]:
            resolved["action"] = (
                state_data["pending_action"]
            )

    return resolved


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

def get_context(
    history: Any,
    **kwargs,
) -> Dict[str, Any]:

    return get_state(
        history,
        **kwargs,
    )


def build_context(
    history: Any,
    **kwargs,
) -> Dict[str, Any]:

    return get_state(
        history,
        **kwargs,
    )


def resolve_context(
    text: str,
    history: Any = None,
    state: Any = None,
) -> Dict[str, Any]:

    return resolve_best_context(
        text,
        history=history,
        state=state,
    )


# ============================================================
# SERIALIZATION
# ============================================================

def state_to_dict(
    state: Any,
) -> Dict[str, Any]:

    return _state_to_dict(state)


def state_from_dict(
    data: Any,
) -> ConversationState:

    if not isinstance(data, dict):
        return ConversationState()

    allowed = {
        key: value
        for key, value in data.items()
        if key in ConversationState.__dataclass_fields__
    }

    return ConversationState(
        **allowed
    )


# ============================================================
# MODULE INFO
# ============================================================

CONTEXT_MANAGER_NAME = (
    "MINH MINI CONTEXT MANAGER FINAL"
)

CONTEXT_MANAGER_VERSION = "FINAL"


if __name__ == "__main__":
    print("=" * 60)
    print(CONTEXT_MANAGER_NAME)
    print("=" * 60)
    print("Version:", CONTEXT_MANAGER_VERSION)
    print("Status : READY")