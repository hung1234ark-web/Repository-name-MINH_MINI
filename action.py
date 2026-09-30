# ============================================================
# MINH MINI — ACTION FINAL
#
# Lớp Action:
# Brain
#   ↓
# Execution Controller
#   ↓
# Action
#   ↓
# App Bridge
#   ↓
# Windows / Browser
#
# Nhiệm vụ:
# - Nhận hành động đã được Brain xác định.
# - Chuyển hành động tới App Bridge.
# - Chuẩn hóa kết quả.
# - Không tự suy luận hội thoại.
# - Không tự gọi Ollama.
# - Không tự tìm kiếm web trừ khi lệnh yêu cầu search.
# - Không báo thành công nếu App Bridge thất bại.
# ============================================================

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

try:
    import app_bridge
except Exception:
    app_bridge = None


# ============================================================
# RESULT
# ============================================================

class ActionResult:
    def __init__(
        self,
        success: bool = False,
        action: str = "",
        target: str = "",
        message: str = "",
        error: str = "",
        data: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:

        self.success = bool(success)
        self.action = str(action or "")
        self.target = str(target or "")
        self.message = str(message or "")
        self.error = str(error or "")
        self.data = data

        self.metadata = (
            metadata
            if isinstance(metadata, dict)
            else {}
        )

    def __bool__(self) -> bool:
        return self.success

    def __str__(self) -> str:
        return (
            self.message
            or self.error
        )

    @property
    def text(self) -> str:
        return str(self)


# ============================================================
# HELPERS
# ============================================================

def normalize_space(
    text: Any,
) -> str:

    return " ".join(
        str(text or "")
        .strip()
        .split()
    )


def text_from_result(
    value: Any,
) -> str:

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if is_dataclass(value):

        try:
            data = asdict(value)

            for key in (
                "message",
                "text",
                "result",
                "response",
                "output",
                "answer",
            ):

                candidate = data.get(
                    key
                )

                if (
                    isinstance(
                        candidate,
                        str,
                    )
                    and candidate.strip()
                ):
                    return candidate.strip()

        except Exception:
            pass

    if isinstance(
        value,
        dict,
    ):

        for key in (
            "message",
            "text",
            "result",
            "response",
            "output",
            "answer",
            "content",
        ):

            candidate = value.get(
                key
            )

            if (
                isinstance(
                    candidate,
                    str,
                )
                and candidate.strip()
            ):
                return candidate.strip()

    for key in (
        "message",
        "text",
        "result",
        "response",
        "output",
        "answer",
    ):

        try:

            candidate = getattr(
                value,
                key,
                None,
            )

            if (
                isinstance(
                    candidate,
                    str,
                )
                and candidate.strip()
            ):
                return candidate.strip()

        except Exception:
            pass

    try:
        return str(value).strip()
    except Exception:
        return ""


def value_from_result(
    value: Any,
    key: str,
    default: Any = None,
) -> Any:

    if isinstance(
        value,
        dict,
    ):
        return value.get(
            key,
            default,
        )

    try:
        result = getattr(
            value,
            key,
            default,
        )

        return result

    except Exception:
        return default


# ============================================================
# RESULT NORMALIZATION
# ============================================================

def normalize_result(
    raw: Any,
    *,
    action: str = "",
    target: str = "",
) -> ActionResult:

    if isinstance(
        raw,
        ActionResult,
    ):

        if not raw.action:
            raw.action = action

        if not raw.target:
            raw.target = target

        return raw

    # --------------------------------------------------------
    # app_bridge.AppBridgeResult
    # --------------------------------------------------------

    if raw is not None:

        success_value = value_from_result(
            raw,
            "success",
            None,
        )

        if success_value is not None:

            message = text_from_result(
                raw
            )

            error = text_from_result(
                value_from_result(
                    raw,
                    "error",
                    "",
                )
            )

            raw_action = (
                value_from_result(
                    raw,
                    "action",
                    action,
                )
                or action
            )

            raw_target = (
                value_from_result(
                    raw,
                    "target",
                    target,
                )
                or target
            )

            data = value_from_result(
                raw,
                "data",
                None,
            )

            metadata = value_from_result(
                raw,
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            return ActionResult(
                success=bool(
                    success_value
                ),
                action=str(
                    raw_action
                    or ""
                ),
                target=str(
                    raw_target
                    or ""
                ),
                message=message,
                error=error,
                data=data,
                metadata={
                    **metadata,
                    "real_execution":
                        bool(
                            success_value
                        ),
                },
            )

    # --------------------------------------------------------
    # bool
    # --------------------------------------------------------

    if isinstance(
        raw,
        bool,
    ):

        return ActionResult(
            success=raw,
            action=action,
            target=target,
            message=(
                "Thao tác đã hoàn tất."
                if raw
                else ""
            ),
            error=(
                ""
                if raw
                else "Thao tác thất bại."
            ),
            metadata={
                "real_execution":
                    raw
            },
        )

    # --------------------------------------------------------
    # None
    # --------------------------------------------------------

    if raw is None:

        return ActionResult(
            success=False,
            action=action,
            target=target,
            error=(
                "Action không nhận được "
                "kết quả từ App Bridge."
            ),
            metadata={
                "real_execution":
                    False
            },
        )

    # --------------------------------------------------------
    # string
    # --------------------------------------------------------

    text = text_from_result(
        raw
    )

    if not text:

        return ActionResult(
            success=False,
            action=action,
            target=target,
            error=(
                "App Bridge trả về kết quả rỗng."
            ),
            metadata={
                "real_execution":
                    False
            },
        )

    lowered = text.lower()

    failure_markers = (
        "không mở được",
        "không thể",
        "không tìm được",
        "không tìm thấy",
        "không thực hiện được",
        "chưa xác định",
        "chưa hỗ trợ",
        "error",
        "failed",
        "exception",
    )

    is_failure = any(
        marker in lowered
        for marker in failure_markers
    )

    if is_failure:

        return ActionResult(
            success=False,
            action=action,
            target=target,
            message=text,
            error=text,
            metadata={
                "real_execution":
                    False
            },
        )

    return ActionResult(
        success=True,
        action=action,
        target=target,
        message=text,
        metadata={
            "real_execution":
                True
        },
    )


# ============================================================
# APP BRIDGE CHECK
# ============================================================

def available() -> bool:
    return (
        app_bridge is not None
    )


# ============================================================
# LOW-LEVEL BRIDGE CALL
# ============================================================

def bridge_call(
    command: str,
) -> ActionResult:

    if app_bridge is None:

        return ActionResult(
            success=False,
            action="bridge",
            target=command,
            error=(
                "app_bridge.py chưa sẵn sàng."
            ),
            metadata={
                "real_execution":
                    False
            },
        )

    handler = getattr(
        app_bridge,
        "handle_command",
        None,
    )

    if not callable(handler):

        handler = getattr(
            app_bridge,
            "execute",
            None,
        )

    if not callable(handler):

        handler = getattr(
            app_bridge,
            "run",
            None,
        )

    if not callable(handler):

        return ActionResult(
            success=False,
            action="bridge",
            target=command,
            error=(
                "Không tìm thấy API thực thi "
                "trong app_bridge.py."
            ),
            metadata={
                "real_execution":
                    False
            },
        )

    try:

        raw = handler(
            command
        )

    except TypeError:

        try:

            raw = handler(
                command=command
            )

        except Exception as exc:

            return ActionResult(
                success=False,
                action="bridge",
                target=command,
                error=str(exc),
                metadata={
                    "real_execution":
                        False
                },
            )

    except Exception as exc:

        return ActionResult(
            success=False,
            action="bridge",
            target=command,
            error=str(exc),
            metadata={
                "real_execution":
                    False
            },
        )

    return normalize_result(
        raw,
        action="bridge",
        target=command,
    )


# ============================================================
# DIRECT ACTIONS
# ============================================================

def open_target(
    target: str,
) -> ActionResult:

    value = normalize_space(
        target
    )

    if not value:

        return ActionResult(
            success=False,
            action="open",
            error=(
                "Lam chưa nói Minh mở gì."
            ),
        )

    if app_bridge is not None:

        handler = getattr(
            app_bridge,
            "open_target",
            None,
        )

        if callable(handler):

            try:

                raw = handler(
                    value
                )

                return normalize_result(
                    raw,
                    action="open",
                    target=value,
                )

            except Exception as exc:

                return ActionResult(
                    success=False,
                    action="open",
                    target=value,
                    error=str(exc),
                    metadata={
                        "real_execution":
                            False
                    },
                )

    return bridge_call(
        f"mở {value}"
    )


def close_target(
    target: str,
) -> ActionResult:

    value = normalize_space(
        target
    )

    if not value:

        return ActionResult(
            success=False,
            action="close",
            error=(
                "Lam chưa nói Minh đóng gì."
            ),
        )

    if app_bridge is not None:

        handler = getattr(
            app_bridge,
            "close_application",
            None,
        )

        if callable(handler):

            try:

                raw = handler(
                    value
                )

                return normalize_result(
                    raw,
                    action="close",
                    target=value,
                )

            except Exception as exc:

                return ActionResult(
                    success=False,
                    action="close",
                    target=value,
                    error=str(exc),
                    metadata={
                        "real_execution":
                            False
                    },
                )

    return bridge_call(
        f"đóng {value}"
    )


def search_google(
    query: str,
) -> ActionResult:

    value = normalize_space(
        query
    )

    if not value:

        return ActionResult(
            success=False,
            action="search_google",
            error=(
                "Lam chưa đưa nội dung cần tìm."
            ),
        )

    if app_bridge is not None:

        handler = getattr(
            app_bridge,
            "search_google",
            None,
        )

        if callable(handler):

            try:

                raw = handler(
                    value
                )

                return normalize_result(
                    raw,
                    action="search_google",
                    target=value,
                )

            except Exception as exc:

                return ActionResult(
                    success=False,
                    action="search_google",
                    target=value,
                    error=str(exc),
                    metadata={
                        "real_execution":
                            False
                    },
                )

    return bridge_call(
        f"tìm google {value}"
    )


def search_youtube(
    query: str,
) -> ActionResult:

    value = normalize_space(
        query
    )

    if not value:

        return ActionResult(
            success=False,
            action="search_youtube",
            error=(
                "Lam chưa đưa nội dung cần tìm."
            ),
        )

    if app_bridge is not None:

        handler = getattr(
            app_bridge,
            "search_youtube",
            None,
        )

        if callable(handler):

            try:

                raw = handler(
                    value
                )

                return normalize_result(
                    raw,
                    action="search_youtube",
                    target=value,
                )

            except Exception as exc:

                return ActionResult(
                    success=False,
                    action="search_youtube",
                    target=value,
                    error=str(exc),
                    metadata={
                        "real_execution":
                            False
                    },
                )

    return bridge_call(
        f"tìm youtube {value}"
    )


def open_url(
    url: str,
) -> ActionResult:

    value = normalize_space(
        url
    )

    if not value:

        return ActionResult(
            success=False,
            action="open_url",
            error="URL trống.",
        )

    if app_bridge is not None:

        handler = getattr(
            app_bridge,
            "open_url",
            None,
        )

        if callable(handler):

            try:

                raw = handler(
                    value
                )

                return normalize_result(
                    raw,
                    action="open_url",
                    target=value,
                )

            except Exception as exc:

                return ActionResult(
                    success=False,
                    action="open_url",
                    target=value,
                    error=str(exc),
                    metadata={
                        "real_execution":
                            False
                    },
                )

    return bridge_call(
        value
    )


# ============================================================
# COMMAND DISPATCH
# ============================================================

def dispatch(
    command: Any,
    *,
    action: str = "",
    target: str = "",
    query: str = "",
    **kwargs: Any,
) -> ActionResult:

    text = normalize_space(
        command
    )

    action_key = (
        normalize_space(action)
        .lower()
    )

    target_value = normalize_space(
        target
    )

    query_value = normalize_space(
        query
    )

    # --------------------------------------------------------
    # Explicit action
    # --------------------------------------------------------

    if action_key in {
        "open",
        "launch",
        "run",
    }:

        return open_target(
            target_value or text
        )

    if action_key in {
        "close",
        "exit",
    }:

        return close_target(
            target_value or text
        )

    if action_key in {
        "search_google",
        "google_search",
    }:

        return search_google(
            query_value
            or target_value
            or text
        )

    if action_key in {
        "search_youtube",
        "youtube_search",
    }:

        return search_youtube(
            query_value
            or target_value
            or text
        )

    if action_key in {
        "open_url",
        "url",
    }:

        return open_url(
            target_value
            or query_value
            or text
        )

    # --------------------------------------------------------
    # Không có explicit action:
    # giao nguyên câu cho App Bridge.
    # --------------------------------------------------------

    if text:

        return bridge_call(
            text
        )

    return ActionResult(
        success=False,
        action=action_key,
        target=target_value,
        error=(
            "Không có lệnh hành động."
        ),
    )


# ============================================================
# MAIN PUBLIC API
# ============================================================

def handle_action_command(
    command: Any,
    decision: Any = None,
    message: str = "",
    target: str = "",
    query: str = "",
    action: str = "",
    **kwargs: Any,
) -> ActionResult:

    # --------------------------------------------------------
    # Nếu Controller truyền decision,
    # ưu tiên thông tin đã được Brain xác định.
    # --------------------------------------------------------

    if decision is not None:

        if not action:

            action = str(
                getattr(
                    decision,
                    "action",
                    "",
                )
                or ""
            )

        if not target:

            target = str(
                getattr(
                    decision,
                    "target",
                    "",
                )
                or ""
            )

        if not query:

            query = str(
                getattr(
                    decision,
                    "query",
                    "",
                )
                or ""
            )

        if not command:

            command = (
                getattr(
                    decision,
                    "original_text",
                    "",
                )
                or getattr(
                    decision,
                    "normalized_text",
                    "",
                )
                or ""
            )

    if not command and message:
        command = message

    return dispatch(
        command,
        action=action,
        target=target,
        query=query,
        **kwargs,
    )


# ============================================================
# COMPATIBILITY
# ============================================================

def execute_action(
    command: Any,
    **kwargs: Any,
) -> ActionResult:

    return handle_action_command(
        command,
        **kwargs,
    )


def execute(
    command: Any,
    **kwargs: Any,
) -> ActionResult:

    return handle_action_command(
        command,
        **kwargs,
    )


def run(
    command: Any,
    **kwargs: Any,
) -> ActionResult:

    return handle_action_command(
        command,
        **kwargs,
    )


def action(
    command: Any,
    **kwargs: Any,
) -> ActionResult:

    return handle_action_command(
        command,
        **kwargs,
    )


# ============================================================
# INFO
# ============================================================

def describe() -> dict[str, Any]:

    return {
        "module":
            "MINH MINI — ACTION FINAL",

        "app_bridge":
            app_bridge is not None,

        "real_execution":
            True,

        "public_functions": [
            "handle_action_command",
            "execute_action",
            "execute",
            "run",
            "action",
            "dispatch",
            "open_target",
            "close_target",
            "search_google",
            "search_youtube",
            "open_url",
        ],
    }


# ============================================================
# SELF CHECK
# ============================================================

def _self_check() -> bool:

    # Không mở ứng dụng thật.
    # Chỉ kiểm tra module và API.

    assert isinstance(
        describe(),
        dict,
    )

    assert callable(
        handle_action_command
    )

    assert callable(
        dispatch
    )

    assert callable(
        open_target
    )

    assert callable(
        close_target
    )

    # Không có command phải fail an toàn.
    result = dispatch("")

    assert result.success is False

    # Không có target phải fail an toàn.
    result = open_target("")

    assert result.success is False

    # Không có query phải fail an toàn.
    result = search_google("")

    assert result.success is False

    return True


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":

    try:

        _self_check()

        print(
            "ACTION FINAL: READY"
        )

    except Exception as exc:

        print(
            "ACTION FINAL: "
            f"ERROR: {exc}"
        )