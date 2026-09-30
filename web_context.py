# ============================================================
# MINH MINI — WEB CONTEXT FINAL
#
# Nhiệm vụ:
# - Lưu kết quả tìm kiếm web hiện tại.
# - Đánh số nguồn.
# - Nhớ nguồn đang được chọn.
# - Nhớ query gần nhất.
# - Hỗ trợ:
#       "nguồn 2"
#       "cái 2"
#       "mở nguồn 2"
#       "nguồn kia"
#       "mở nó"
#       "tìm thêm"
# - Không tự tìm web.
# - Không tự mở trình duyệt.
# - Không tự gọi Ollama.
#
# Web Search = lấy dữ liệu
# Web Context = nhớ và truy xuất dữ liệu
# Web AI = tổng hợp dữ liệu
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================
# RESULT / SOURCE
# ============================================================

@dataclass
class WebSource:
    number: int = 0
    title: str = ""
    url: str = ""
    snippet: str = ""
    description: str = ""
    data: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "description": self.description,
            "data": self.data,
        }


@dataclass
class WebContextState:
    query: str = ""
    results: list[WebSource] = field(
        default_factory=list
    )
    selected_source_number: int | None = None
    selected_source: WebSource | None = None
    last_action: str = ""
    last_reference: str = ""
    turn_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "results": [
                item.to_dict()
                for item in self.results
            ],
            "selected_source_number":
                self.selected_source_number,
            "selected_source":
                (
                    self.selected_source.to_dict()
                    if self.selected_source
                    else None
                ),
            "last_action": self.last_action,
            "last_reference":
                self.last_reference,
            "turn_count": self.turn_count,
        }


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_space(
    value: Any,
) -> str:
    return " ".join(
        str(value or "")
        .strip()
        .split()
    )


def lowered(
    value: Any,
) -> str:
    return normalize_space(
        value
    ).lower()


def text_value(
    value: Any,
) -> str:
    if value is None:
        return ""

    if isinstance(
        value,
        str,
    ):
        return value.strip()

    try:
        return str(value).strip()
    except Exception:
        return ""


# ============================================================
# INTERNAL STATE
# ============================================================

_STATE = WebContextState()


# ============================================================
# SOURCE NORMALIZATION
# ============================================================

def normalize_source(
    raw: Any,
    number: int,
) -> WebSource:

    if isinstance(
        raw,
        WebSource,
    ):
        raw.number = number
        return raw

    if isinstance(
        raw,
        dict,
    ):

        title = (
            raw.get("title")
            or raw.get("name")
            or raw.get("headline")
            or f"Nguồn {number}"
        )

        url = (
            raw.get("url")
            or raw.get("link")
            or raw.get("href")
            or ""
        )

        snippet = (
            raw.get("snippet")
            or raw.get("summary")
            or raw.get("text")
            or ""
        )

        description = (
            raw.get("description")
            or ""
        )

        return WebSource(
            number=number,
            title=text_value(title),
            url=text_value(url),
            snippet=text_value(snippet),
            description=text_value(
                description
            ),
            data=dict(raw),
        )

    text = text_value(raw)

    return WebSource(
        number=number,
        title=text or f"Nguồn {number}",
        snippet=text,

    )


# ============================================================
# STORE SEARCH
# ============================================================

def store_results(
    query: str,
    results: Any,
) -> WebContextState:

    global _STATE

    query_text = normalize_space(
        query
    )

    if results is None:
        results = []

    if isinstance(
        results,
        dict,
    ):

        for key in (
            "results",
            "items",
            "sources",
            "data",
        ):

            candidate = results.get(
                key
            )

            if isinstance(
                candidate,
                list,
            ):
                results = candidate
                break

        else:
            results = [results]

    if not isinstance(
        results,
        list,
    ):
        results = [results]

    sources: list[WebSource] = []

    for index, item in enumerate(
        results,
        start=1,
    ):

        try:
            source = normalize_source(
                item,
                index,
            )

            sources.append(
                source
            )

        except Exception:
            continue

    _STATE.query = query_text
    _STATE.results = sources
    _STATE.selected_source_number = None
    _STATE.selected_source = None
    _STATE.last_action = "search"
    _STATE.last_reference = ""
    _STATE.turn_count += 1

    return _STATE


def clear() -> None:

    global _STATE

    _STATE = WebContextState()


# ============================================================
# QUERY
# ============================================================

def get_query() -> str:
    return _STATE.query


def set_query(
    query: str,
) -> None:

    _STATE.query = normalize_space(
        query
    )


# ============================================================
# RESULTS
# ============================================================

def get_results() -> list[WebSource]:
    return list(
        _STATE.results
    )


def result_count() -> int:
    return len(
        _STATE.results
    )


def has_results() -> bool:
    return bool(
        _STATE.results
    )


def get_all_sources() -> list[dict[str, Any]]:
    return [
        source.to_dict()
        for source in _STATE.results
    ]


# ============================================================
# SOURCE LOOKUP
# ============================================================

def get_source(
    number: int | str,
) -> WebSource | None:

    try:
        index = int(number)

    except Exception:
        return None

    if index < 1:
        return None

    if (
        index
        > len(_STATE.results)
    ):
        return None

    return _STATE.results[
        index - 1
    ]


def get_source_dict(
    number: int | str,
) -> dict[str, Any] | None:

    source = get_source(
        number
    )

    if source is None:
        return None

    return source.to_dict()


def select_source(
    number: int | str,
) -> WebSource | None:

    global _STATE

    source = get_source(
        number
    )

    if source is None:
        return None

    _STATE.selected_source_number = (
        source.number
    )

    _STATE.selected_source = source

    _STATE.last_action = (
        "select_source"
    )

    _STATE.last_reference = (
        f"source:{source.number}"
    )

    _STATE.turn_count += 1

    return source


def get_selected_source() -> WebSource | None:
    return _STATE.selected_source


def get_selected_source_number() -> int | None:
    return (
        _STATE.selected_source_number
    )


# ============================================================
# REFERENCE DETECTION
# ============================================================

def extract_number(
    text: str,
) -> int | None:

    value = lowered(
        text
    )

    # "nguồn 2"
    # "source 2"
    # "cái 2"
    # "số 2"
    # "2"
    patterns = (
        r"^(?:nguồn|source|cái|số)\s*(\d{1,2})$",
        r"^(\d{1,2})$",
    )

    import re

    for pattern in patterns:

        match = re.search(
            pattern,
            value,
        )

        if match:

            try:
                return int(
                    match.group(1)
                )

            except Exception:
                return None

    return None


def is_current_source_reference(
    text: str,
) -> bool:

    value = lowered(
        text
    )

    return value in {
        "nó",
        "cái này",
        "nguồn này",
        "source này",
        "cái đó",
        "nguồn đó",
        "source đó",
    }


def is_previous_source_reference(
    text: str,
) -> bool:

    value = lowered(
        text
    )

    return value in {
        "cái kia",
        "nguồn kia",
        "source kia",
        "còn cái kia",
        "nguồn còn lại",
        "cái còn lại",
    }


def is_more_search(
    text: str,
) -> bool:

    value = lowered(
        text
    )

    return value in {
        "tìm thêm",
        "tìm thêm nữa",
        "xem thêm",
        "thêm nữa",
        "còn gì nữa",
        "có gì thêm",
    }


# ============================================================
# SMART REFERENCE
# ============================================================

def resolve_reference(
    text: str,
) -> WebSource | None:

    value = normalize_space(
        text
    )

    # explicit number
    number = extract_number(
        value
    )

    if number is not None:

        source = select_source(
            number
        )

        return source

    # current selected
    if is_current_source_reference(
        value
    ):

        if _STATE.selected_source:
            return _STATE.selected_source

    # "cái kia"
    if is_previous_source_reference(
        value
    ):

        if (
            _STATE.selected_source_number
            and len(_STATE.results) >= 2
        ):

            current = (
                _STATE.selected_source_number
            )

            # ưu tiên nguồn ngay trước đó
            candidates = [
                current - 1,
                current + 1,
            ]

            for number in candidates:

                if (
                    1
                    <= number
                    <= len(_STATE.results)
                ):

                    return select_source(
                        number
                    )

        # chưa chọn gì:
        # "cái kia" -> nguồn 2 nếu có
        if len(_STATE.results) >= 2:

            return select_source(
                2
            )

    return None


def resolve_best_source(
    text: str,
) -> WebSource | None:

    # 1. explicit
    source = resolve_reference(
        text
    )

    if source is not None:
        return source

    value = lowered(
        text
    )

    # 2. "mở nó"
    if value in {
        "mở nó",
        "open it",
        "mở cái này",
        "mở nguồn này",
        "mở cái đó",
        "mở nguồn đó",
    }:

        if _STATE.selected_source:
            return _STATE.selected_source

    # 3. không nói rõ -> giữ selected source
    if _STATE.selected_source:
        return _STATE.selected_source

    return None


# ============================================================
# SOURCE DESCRIPTION
# ============================================================

def format_source(
    source: WebSource | None,
) -> str:

    if source is None:
        return ""

    lines = [
        f"Nguồn {source.number}: "
        f"{source.title}"
    ]

    if source.snippet:
        lines.append(
            source.snippet
        )

    if source.url:
        lines.append(
            source.url
        )

    return "\n".join(
        lines
    )


def format_sources(
    limit: int = 10,
) -> str:

    lines: list[str] = []

    for source in _STATE.results[
        :limit
    ]:

        line = (
            f"{source.number}. "
            f"{source.title}"
        )

        if source.snippet:
            line += (
                f"\n   {source.snippet}"
            )

        if source.url:
            line += (
                f"\n   {source.url}"
            )

        lines.append(
            line
        )

    return "\n".join(
        lines
    )


# ============================================================
# CURRENT CONTEXT
# ============================================================

def current_context() -> dict[str, Any]:

    return _STATE.to_dict()


def state() -> WebContextState:

    return _STATE


# ============================================================
# ACTION MEMORY
# ============================================================

def mark_action(
    action: str,
    reference: str = "",
) -> None:

    _STATE.last_action = normalize_space(
        action
    )

    if reference:
        _STATE.last_reference = (
            normalize_space(
                reference
            )
        )

    _STATE.turn_count += 1


def get_last_action() -> str:
    return _STATE.last_action


def get_last_reference() -> str:
    return _STATE.last_reference


# ============================================================
# OPEN / SOURCE DECISION HELPERS
# ============================================================

def source_url(
    number: int | str | None = None,
) -> str:

    if number is None:
        source = (
            _STATE.selected_source
        )
    else:
        source = get_source(
            number
        )

    if source is None:
        return ""

    return source.url


def source_title(
    number: int | str | None = None,
) -> str:

    if number is None:
        source = (
            _STATE.selected_source
        )
    else:
        source = get_source(
            number
        )

    if source is None:
        return ""

    return source.title


# ============================================================
# SERIALIZATION
# ============================================================

def to_dict() -> dict[str, Any]:
    return _STATE.to_dict()


def from_dict(
    data: Any,
) -> WebContextState:

    global _STATE

    if not isinstance(
        data,
        dict,
    ):
        clear()
        return _STATE

    query = data.get(
        "query",
        "",
    )

    raw_results = data.get(
        "results",
        [],
    )

    new_state = WebContextState(
        query=text_value(
            query
        ),
    )

    if not isinstance(
        raw_results,
        list,
    ):
        raw_results = []

    for index, item in enumerate(
        raw_results,
        start=1,
    ):

        source = normalize_source(
            item,
            index,
        )

        new_state.results.append(
            source
        )

    selected_number = data.get(
        "selected_source_number"
    )

    if selected_number is not None:

        try:
            selected_number = int(
                selected_number
            )

        except Exception:
            selected_number = None

    new_state.selected_source_number = (
        selected_number
    )

    if selected_number is not None:

        new_state.selected_source = (
            get_from_list(
                new_state.results,
                selected_number,
            )
        )

    new_state.last_action = (
        text_value(
            data.get(
                "last_action",
                "",
            )
        )
    )

    new_state.last_reference = (
        text_value(
            data.get(
                "last_reference",
                "",
            )
        )
    )

    new_state.turn_count = int(
        data.get(
            "turn_count",
            0,
        )
        or 0
    )

    _STATE = new_state

    return _STATE


def get_from_list(
    values: list[WebSource],
    number: int,
) -> WebSource | None:

    if number < 1:
        return None

    if number > len(values):
        return None

    return values[
        number - 1
    ]


# ============================================================
# CLEAR SELECTION
# ============================================================

def clear_selection() -> None:

    _STATE.selected_source_number = None
    _STATE.selected_source = None
    _STATE.last_reference = ""
    _STATE.last_action = (
        "clear_selection"
    )


# ============================================================
# INFO
# ============================================================

def describe() -> dict[str, Any]:

    return {
        "module":
            "MINH MINI — WEB CONTEXT FINAL",

        "query":
            _STATE.query,

        "result_count":
            len(_STATE.results),

        "selected_source_number":
            _STATE.selected_source_number,

        "last_action":
            _STATE.last_action,

        "last_reference":
            _STATE.last_reference,

        "public_functions": [
            "store_results",
            "clear",
            "get_query",
            "set_query",
            "get_results",
            "result_count",
            "has_results",
            "get_all_sources",
            "get_source",
            "get_source_dict",
            "select_source",
            "get_selected_source",
            "get_selected_source_number",
            "extract_number",
            "resolve_reference",
            "resolve_best_source",
            "format_source",
            "format_sources",
            "current_context",
            "state",
            "mark_action",
            "get_last_action",
            "get_last_reference",
            "source_url",
            "source_title",
            "to_dict",
            "from_dict",
            "clear_selection",
        ],
    }


# ============================================================
# SELF CHECK
# ============================================================

def _self_check() -> bool:

    clear()

    store_results(
        "giá iphone mới nhất",
        [
            {
                "title": "Nguồn A",
                "url": "https://example.com/a",
                "snippet": "Thông tin A",
            },
            {
                "title": "Nguồn B",
                "url": "https://example.com/b",
                "snippet": "Thông tin B",
            },
            {
                "title": "Nguồn C",
                "url": "https://example.com/c",
                "snippet": "Thông tin C",
            },
        ],
    )

    assert (
        result_count()
        == 3
    )

    assert (
        get_query()
        == "giá iphone mới nhất"
    )

    source = get_source(
        2
    )

    assert source is not None
    assert source.number == 2
    assert source.title == "Nguồn B"

    selected = select_source(
        2
    )

    assert selected is not None
    assert (
        get_selected_source_number()
        == 2
    )

    assert (
        extract_number("nguồn 2")
        == 2
    )

    assert (
        extract_number("cái 3")
        == 3
    )

    assert (
        extract_number("2")
        == 2
    )

    assert is_current_source_reference(
        "mở nó"
    )

    # "cái kia" từ nguồn 2 -> nguồn 1
    previous = resolve_reference(
        "cái kia"
    )

    assert previous is not None
    assert previous.number == 1

    # reset
    clear()

    assert not has_results()

    return True


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":

    try:

        _self_check()

        print(
            "WEB CONTEXT FINAL: READY"
        )

    except Exception as exc:

        print(
            "WEB CONTEXT FINAL: "
            f"ERROR: {exc}"
        )