# ============================================================
# MINH MINI / ÁNH
# UNDERSTANDING — SHARED CONVERSATION STATE
# ============================================================

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional

import conversation_state


# ============================================================
# NORMALIZATION
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


def normalize_spaces(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(text or "").strip(),
    )


def remove_accents(text: str) -> str:
    text = unicodedata.normalize(
        "NFD",
        str(text or ""),
    )

    chars = []

    for char in text:
        if unicodedata.category(char) != "Mn":
            chars.append(char)

    return "".join(chars).replace(
        "đ",
        "d",
    ).replace(
        "Đ",
        "D",
    )


def normalize_typo(text: str) -> str:
    result = normalize_spaces(text)

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

    return normalize_spaces(result)


def normalize_key(text: str) -> str:
    return normalize_spaces(
        remove_accents(
            normalize_typo(text)
        ).lower()
    )


# ============================================================
# BASIC DETECTION
# ============================================================

ACTION_STARTERS = (
    "mở ",
    "vào ",
    "truy cập ",
    "chạy ",
    "bật ",
    "đóng ",
    "tắt ",
    "lưu ",
    "xóa ",
    "tạo ",
    "đọc ",
    "viết ",
    "tính ",
)

WEB_STARTERS = (
    "tìm ",
    "tìm kiếm ",
    "tra cứu ",
    "search ",
)

QUESTION_STARTERS = (
    "ai ",
    "tại sao ",
    "vì sao ",
    "thế nào ",
    "làm sao ",
    "có phải ",
    "bao nhiêu ",
    "là gì ",
    "ở đâu ",
    "khi nào ",
    "giá ",
)


REFERENCE_WORDS = {
    "nó",
    "cái đó",
    "cái này",
    "cái ấy",
    "chỗ đó",
    "chỗ này",
    "người đó",
    "món đó",
    "con đó",
    "cái vừa nói",
    "cái lúc nãy",
    "nãy",
    "đó",
    "này",
}


TARGET_ALIASES = {
    "google": "google",
    "gg": "google",
    "chrome": "chrome",
    "google chrome": "chrome",
    "youtube": "youtube",
    "yt": "youtube",
    "ytb": "youtube",
    "facebook": "facebook",
    "fb": "facebook",
    "notepad": "notepad",
    "calculator": "calculator",
    "calc": "calculator",
    "paint": "paint",
    "explorer": "explorer",
    "desktop": "desktop",
    "download": "downloads",
    "downloads": "downloads",
    "documents": "documents",
    "pictures": "pictures",
    "videos": "videos",
    "music": "music",
    "home": "home",
}


def is_question_text(text: str) -> bool:
    normalized = normalize_typo(text)
    key = normalize_key(normalized)

    if "?" in normalized:
        return True

    if key.startswith(
        tuple(
            normalize_key(item)
            for item in QUESTION_STARTERS
        )
    ):
        return True

    price_words = (
        "gia",
        "bao nhieu",
        "bao nhieu tien",
    )

    return any(
        key == word
        or key.startswith(word + " ")
        for word in price_words
    )


def is_action_text(text: str) -> bool:
    normalized = normalize_typo(text)
    key = normalize_key(normalized)

    action_keys = tuple(
        normalize_key(item)
        for item in ACTION_STARTERS
    )

    return key.startswith(action_keys)


def is_web_text(text: str) -> bool:
    normalized = normalize_typo(text)
    key = normalize_key(normalized)

    if key.startswith(
        tuple(
            normalize_key(item)
            for item in WEB_STARTERS
        )
    ):
        return True

    web_markers = (
        "tren web",
        "tren mang",
        "internet",
        "moi nhat",
        "tin tuc",
        "thoi tiet",
        "gia",
        "tim gia",
        "tra cuu",
    )

    return any(
        marker in key
        for marker in web_markers
    )


# ============================================================
# ENTITY EXTRACTION
# ============================================================

def extract_numbers(text: str) -> List[float]:
    values: List[float] = []

    for match in re.findall(
        r"\d+(?:[.,]\d+)?",
        text,
    ):
        try:
            values.append(
                float(
                    match.replace(",", ".")
                )
            )
        except ValueError:
            continue

    return values


def extract_money(text: str) -> List[str]:
    patterns = (
        r"\d[\d.,]*\s*(?:k|nghin|nghìn|trieu|triệu|ty|tỷ|vnd|đ)",
        r"\d[\d.,]*\s*(?:dong|đồng)",
    )

    result: List[str] = []

    for pattern in patterns:
        result.extend(
            re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )

    return result


def extract_time(text: str) -> Optional[str]:
    match = re.search(
        r"\b(\d{1,2})(?:[:h](\d{1,2}))?\b",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    hour = match.group(1)
    minute = match.group(2)

    if minute is None:
        return f"{hour}:00"

    return f"{hour}:{minute}"


def extract_target(text: str) -> str:
    key = normalize_key(text)

    for alias, target in sorted(
        TARGET_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if key == alias:
            return target

        if key.startswith(alias + " "):
            return target

    return ""


def extract_topic(text: str) -> str:
    normalized = normalize_typo(text).strip()
    key = normalize_key(normalized)

    prefixes = (
        "gia",
        "gia cua",
        "gia bao nhieu",
        "bao nhieu",
        "tim",
        "tim kiem",
        "tra cuu",
        "moi nhat",
    )

    for prefix in sorted(
        prefixes,
        key=len,
        reverse=True,
    ):
        prefix_key = normalize_key(prefix)

        if key == prefix_key:
            return ""

        if key.startswith(prefix_key + " "):

            original_words = normalized.split()
            prefix_words = prefix.split()

            if len(original_words) > len(prefix_words):

                return " ".join(
                    original_words[
                        len(prefix_words):
                    ]
                ).strip()

    return normalized


# ============================================================
# REFERENCE
# ============================================================

def is_reference_text(text: str) -> bool:
    key = normalize_key(text)

    if key in {
        normalize_key(item)
        for item in REFERENCE_WORDS
    }:
        return True

    return (
        key.startswith("con ")
        or key.startswith("còn ")
        or key.startswith("gia ")
        or key.startswith("giá ")
        or key in {
            "bao nhieu",
            "the nao",
            "thế nào",
            "sao",
        }
    )


def find_previous_topic(
    history: Any,
) -> str:

    state = conversation_state.build_state(
        history
    )

    current_topic = conversation_state.get_state_value(
        state,
        "current_topic",
    )

    if current_topic:
        return current_topic

    for item in reversed(
        conversation_state.valid_messages(history)
    ):
        if item["role"] != "user":
            continue

        text = item["content"]

        if conversation_state.looks_like_short_reply(
            text
        ):
            continue

        if is_reference_text(text):
            continue

        topic = extract_topic(text)

        if topic:
            return topic

    return ""


def find_previous_target(
    history: Any,
) -> str:

    state = conversation_state.build_state(
        history
    )

    target = conversation_state.get_state_value(
        state,
        "current_target",
    )

    if target:
        return target

    for item in reversed(
        conversation_state.valid_messages(history)
    ):
        if item["role"] != "user":
            continue

        target = extract_target(
            item["content"]
        )

        if target:
            return target

    return ""


def find_previous_query(
    history: Any,
) -> str:

    state = conversation_state.build_state(
        history
    )

    query = conversation_state.get_state_value(
        state,
        "current_query",
    )

    if query:
        return query

    for item in reversed(
        conversation_state.valid_messages(history)
    ):
        if item["role"] != "user":
            continue

        text = normalize_typo(
            item["content"]
        )

        if normalize_key(text).startswith(
            tuple(
                normalize_key(prefix)
                for prefix in WEB_STARTERS
            )
        ):
            query = extract_topic(text)

            if query:
                return query

    return ""


def find_previous_action(
    history: Any,
) -> str:

    state = conversation_state.build_state(
        history
    )

    action = conversation_state.get_state_value(
        state,
        "current_action",
    )

    if action:
        return action

    for item in reversed(
        conversation_state.valid_messages(history)
    ):
        if item["role"] != "user":
            continue

        text = normalize_typo(
            item["content"]
        )

        if is_action_text(text):
            return text

    return ""


def resolve_reference(
    text: str,
    history: Any,
) -> Dict[str, Any]:

    normalized = normalize_typo(text)
    key = normalize_key(normalized)

    result: Dict[str, Any] = {
        "is_reference": False,
        "reference": "",
        "topic": "",
        "target": "",
        "query": "",
        "action": "",
        "followup_text": normalized,
    }

    if not is_reference_text(normalized):
        return result

    result["is_reference"] = True
    result["reference"] = normalized

    topic = find_previous_topic(
        history
    )

    target = find_previous_target(
        history
    )

    query = find_previous_query(
        history
    )

    action = find_previous_action(
        history
    )

    result["topic"] = topic
    result["target"] = target
    result["query"] = query
    result["action"] = action

    # --------------------------------------------------------
    # PRICE FOLLOW-UP
    # --------------------------------------------------------

    if key in {
        "gia",
        "gia bao nhieu",
        "bao nhieu",
        "bao nhieu tien",
    }:

        if topic:
            result["followup_text"] = (
                f"giá {topic}"
            )

        elif query:
            result["followup_text"] = (
                f"giá {query}"
            )

        return result

    # --------------------------------------------------------
    # WHAT / HOW
    # --------------------------------------------------------

    if key in {
        "the nao",
        "thế nào",
        "sao",
        "con sao",
        "còn sao",
    }:

        if topic:
            result["followup_text"] = (
                f"{topic} thế nào"
            )

        return result

    # --------------------------------------------------------
    # "CÒN ..."
    # --------------------------------------------------------

    if key.startswith(
        "con "
    ) or key.startswith(
        "còn "
    ):

        tail = re.sub(
            r"^(?:con|còn)\s+",
            "",
            normalized,
            flags=re.IGNORECASE,
        ).strip()

        if topic and tail:
            result["followup_text"] = (
                f"{topic} {tail}"
            )

        elif query and tail:
            result["followup_text"] = (
                f"{query} {tail}"
            )

        return result

    # --------------------------------------------------------
    # REFERENCE PRONOUN
    # --------------------------------------------------------

    if key in {
        "no",
        "nó",
        "cai do",
        "cái đó",
        "cai nay",
        "cái này",
        "cai ay",
        "cái ấy",
    }:

        if topic:
            result["followup_text"] = topic

        elif target:
            result["followup_text"] = target

        elif query:
            result["followup_text"] = query

        return result

    return result


def resolve_reference_topic(
    text: str,
    history: Any,
) -> str:

    result = resolve_reference(
        text,
        history,
    )

    return str(
        result.get(
            "topic",
            "",
        )
        or ""
    )


def build_followup_text(
    text: str,
    history: Any,
) -> str:

    result = resolve_reference(
        text,
        history,
    )

    return str(
        result.get(
            "followup_text",
            text,
        )
        or text
    ).strip()


# ============================================================
# INTENT
# ============================================================

def detect_intent(
    text: str,
    *,
    is_question: bool,
    is_action: bool,
    needs_web: bool,
    needs_reference: bool,
) -> str:

    if needs_reference:
        if needs_web:
            return "web_search"

        if is_action:
            return "action"

        return "reference"

    if needs_web:
        return "web_search"

    if is_action:
        return "action"

    if is_question:
        return "question"

    return "chat"


# ============================================================
# MAIN UNDERSTANDING
# ============================================================

def understand(
    text: str,
    history: Any = None,
) -> Dict[str, Any]:

    original = normalize_spaces(text)
    normalized = normalize_typo(original)
    key = normalize_key(normalized)

    history = (
        conversation_state.valid_messages(history)
    )

    shared_state = conversation_state.build_state(
        history,
        current_topic=find_previous_topic(history),
        current_query=find_previous_query(history),
        current_target=find_previous_target(history),
        current_action=find_previous_action(history),
    )

    is_question = is_question_text(
        normalized
    )

    is_action = is_action_text(
        normalized
    )

    needs_web = is_web_text(
        normalized
    )

    reference_info = resolve_reference(
        normalized,
        history,
    )

    needs_reference = bool(
        reference_info.get(
            "is_reference"
        )
    )

    reference_topic = str(
        reference_info.get(
            "topic",
            "",
        )
        or ""
    )

    followup_text = str(
        reference_info.get(
            "followup_text",
            normalized,
        )
        or normalized
    ).strip()

    target = extract_target(
        normalized
    )

    topic = extract_topic(
        normalized
    )

    query = ""

    if (
        key.startswith(
            tuple(
                normalize_key(item)
                for item in WEB_STARTERS
            )
        )
    ):
        query = extract_topic(
            normalized
        )

    if needs_reference:
        if reference_info.get("query"):
            query = str(
                reference_info.get(
                    "query"
                )
            )

    intent = detect_intent(
        normalized,
        is_question=is_question,
        is_action=is_action,
        needs_web=needs_web,
        needs_reference=needs_reference,
    )

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = 0.70

    if intent == "chat":
        confidence = 0.60

    if needs_reference:
        confidence = 0.84

    if needs_web:
        confidence = max(
            confidence,
            0.82,
        )

    if is_action:
        confidence = max(
            confidence,
            0.82,
        )

    # --------------------------------------------------------
    # ENTITIES
    # --------------------------------------------------------

    entities: Dict[str, Any] = {
        "target": target,
        "topic": topic,
        "query": query,
        "money": extract_money(normalized),
        "numbers": extract_numbers(normalized),
        "time": extract_time(normalized),
    }

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    return {
        "original_text": original,
        "normalized_text": normalized,

        "intent": intent,
        "confidence": confidence,

        "is_question": is_question,
        "is_action": is_action,

        "needs_web": needs_web,
        "needs_time": (
            "mấy giờ" in normalized.lower()
            or "mấy h" in normalized.lower()
        ),
        "needs_date": (
            "hôm nay" in normalized.lower()
            or "hôm qua" in normalized.lower()
        ),
        "needs_memory": (
            key.startswith("nho ")
            or key.startswith("luu ")
            or key.startswith("ghi nho ")
        ),

        "needs_reference": needs_reference,

        "action": (
            reference_info.get("action")
            if needs_reference
            else find_previous_action(
                history
            )
            if key in {
                "no",
                "nó",
                "cai do",
                "cái đó",
            }
            else normalized
            if is_action
            else ""
        ),

        "target": target,
        "query": query,
        "topic": topic,

        "reference": reference_info.get(
            "reference",
            "",
        ),
        "reference_topic": reference_topic,
        "followup_text": followup_text,

        "entities": entities,

        "context": shared_state,

        "topics": [
            value
            for value in (
                topic,
                reference_topic,
                target,
            )
            if value
        ],
    }


# ============================================================
# COMPATIBILITY HELPERS
# ============================================================

def get_intent(
    text: str,
    history: Any = None,
) -> str:

    return str(
        understand(
            text,
            history,
        ).get(
            "intent",
            "chat",
        )
    )


def is_action(
    text: str,
    history: Any = None,
) -> bool:

    return bool(
        understand(
            text,
            history,
        ).get(
            "is_action",
            False,
        )
    )


def is_question(
    text: str,
    history: Any = None,
) -> bool:

    return bool(
        understand(
            text,
            history,
        ).get(
            "is_question",
            False,
        )
    )


def get_reference(
    text: str,
    history: Any = None,
) -> Dict[str, Any]:

    result = understand(
        text,
        history,
    )

    return {
        "needs_reference": result.get(
            "needs_reference",
            False,
        ),
        "reference": result.get(
            "reference",
            "",
        ),
        "reference_topic": result.get(
            "reference_topic",
            "",
        ),
        "followup_text": result.get(
            "followup_text",
            "",
        ),
    }


def get_followup_text(
    text: str,
    history: Any = None,
) -> str:

    return str(
        understand(
            text,
            history,
        ).get(
            "followup_text",
            text,
        )
        or text
    )


# ============================================================
# SELF CHECK
# ============================================================

def _self_check() -> None:

    history = [
        {
            "role": "user",
            "content": "Sony ZV-E10",
        },
        {
            "role": "assistant",
            "content": "Đây là máy ảnh Sony.",
        },
    ]

    result = understand(
        "giá",
        history,
    )

    assert result["needs_reference"] is True
    assert "Sony ZV-E10" in result[
        "followup_text"
    ]

    result = understand(
        "mở Google",
        history,
    )

    assert result["is_action"] is True
    assert result["target"] == "google"

    result = understand(
        "tìm giá iPhone mới nhất",
        history,
    )

    assert result["needs_web"] is True
    assert result["query"]

    result = understand(
        "nó",
        history,
    )

    assert result["needs_reference"] is True
    assert result["followup_text"]

    print(
        "UNDERSTANDING — SHARED STATE PASS"
    )


if __name__ == "__main__":
    _self_check()