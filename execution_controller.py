# ============================================================
# MINH MINI — EXECUTION CONTROLLER FINAL
# ============================================================
# Brain / Router -> Execution Controller -> Handler
#
# Nhiệm vụ:
# - Nhận decision đã được Router kiểm tra
# - Chọn đúng handler
# - Truyền metadata an toàn xuống handler
# - Hỗ trợ handler cũ chỉ nhận message
# - Chuẩn hóa kết quả handler
# - Không tự nhận đã thực hiện hành động nếu handler thất bại
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
import inspect


# ============================================================
# HELPERS
# ============================================================

def clean_text(value: Any) -> str:
    """
    Chuyển giá trị thành text sạch.
    """
    if value is None:
        return ""

    try:
        return str(value).strip()
    except Exception:
        return ""


def get_value(
    source: Any,
    key: str,
    default: Any = "",
) -> Any:
    """
    Lấy value an toàn từ dict hoặc object.
    """

    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(key, default)

    try:
        return getattr(source, key, default)
    except Exception:
        return default


# ============================================================
# RESULT
# ============================================================

@dataclass
class ExecutionResult:
    success: bool = False
    response: str = ""

    intent: str = ""
    tool: str = ""
    action: str = ""
    target: str = ""

    error: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# NORMALIZE HANDLER RESULT
# ============================================================

def normalize_handler_result(
    result: Any,
) -> tuple[bool, str, str]:

    # --------------------------------------------------------
    # None
    # --------------------------------------------------------

    if result is None:
        return False, "", ""

    # --------------------------------------------------------
    # ExecutionResult
    # --------------------------------------------------------

    if isinstance(result, ExecutionResult):

        response = clean_text(
            result.response
        )

        return (
            bool(result.success and response),
            response,
            clean_text(result.error),
        )

    # --------------------------------------------------------
    # String
    # --------------------------------------------------------

    if isinstance(result, str):

        response = clean_text(
            result
        )

        if response:
            return (
                True,
                response,
                "",
            )

        return (
            False,
            "",
            "",
        )

    # --------------------------------------------------------
    # Tuple / List
    # --------------------------------------------------------

    if isinstance(result, (tuple, list)):

        if not result:
            return False, "", ""

        success = True
        response = ""
        error = ""

        if len(result) >= 1:
            first = result[0]

            if isinstance(first, bool):
                success = first
            elif isinstance(first, str):
                response = clean_text(first)
            elif first is not None:
                success = bool(first)

        if len(result) >= 2:
            response = clean_text(result[1])

        if len(result) >= 3:
            error = clean_text(result[2])

        if response:
            return (
                bool(success),
                response,
                error,
            )

        return (
            False,
            "",
            error,
        )

    # --------------------------------------------------------
    # Dict
    # --------------------------------------------------------

    if isinstance(result, dict):

        response = ""

        for name in (
            "response",
            "message",
            "text",
            "output",
            "result",
            "answer",
        ):

            value = result.get(
                name,
                None,
            )

            if clean_text(value):
                response = clean_text(
                    value
                )
                break

        success = result.get(
            "success",
            True,
        )

        error = clean_text(
            result.get(
                "error",
                "",
            )
        )

        if response:
            return (
                bool(success),
                response,
                error,
            )

        return (
            False,
            "",
            error,
        )

    # --------------------------------------------------------
    # Object
    # --------------------------------------------------------

    response = ""

    for name in (
        "response",
        "message",
        "text",
        "output",
        "result",
        "answer",
    ):

        try:
            value = getattr(
                result,
                name,
                None,
            )

            if clean_text(value):
                response = clean_text(
                    value
                )
                break

        except Exception:
            continue

    success = getattr(
        result,
        "success",
        True,
    )

    error = clean_text(
        getattr(
            result,
            "error",
            "",
        )
    )

    if response:
        return (
            bool(success),
            response,
            error,
        )

    return (
        False,
        "",
        error,
    )


# ============================================================
# EXECUTION CONTROLLER
# ============================================================

class ExecutionController:

    # --------------------------------------------------------
    # INIT
    # --------------------------------------------------------

    def __init__(
        self,
        handlers: Optional[
            Dict[str, Callable]
        ] = None,
    ):

        self.handlers: Dict[
            str,
            Callable,
        ] = {}

        if handlers:
            self.register_many(
                handlers
            )

    # --------------------------------------------------------
    # REGISTER
    # --------------------------------------------------------

    def register(
        self,
        name: str,
        handler: Callable,
    ) -> None:

        key = clean_text(
            name
        ).lower()

        if not key:
            return

        if not callable(handler):
            raise TypeError(
                f"Handler '{key}' must be callable."
            )

        self.handlers[key] = handler

    # --------------------------------------------------------
    # REGISTER MANY
    # --------------------------------------------------------

    def register_many(
        self,
        handlers: Dict[str, Callable],
    ) -> None:

        if not isinstance(
            handlers,
            dict,
        ):
            return

        for name, handler in handlers.items():
            self.register(
                name,
                handler,
            )

    # --------------------------------------------------------
    # GET HANDLER
    # --------------------------------------------------------

    def get_handler(
        self,
        name: str,
    ) -> Optional[Callable]:

        key = clean_text(
            name
        ).lower()

        if not key:
            return None

        handler = self.handlers.get(
            key
        )

        if callable(handler):
            return handler

        return None

    # ========================================================
    # CALL HANDLER
    # ========================================================

    def _call_handler(
        self,
        handler: Callable,
        message: str = "",
        **kwargs: Any,
    ) -> Any:
        """
        Gọi handler.

        Ưu tiên:
            handler(message, **kwargs)

        Nếu handler không hỗ trợ keyword:
            handler(message)

        Đây là điểm sửa lỗi chính của bản FINAL.
        """

        if not callable(handler):
            raise TypeError(
                "handler is not callable"
            )

        message = clean_text(
            message
        )

        # ----------------------------------------------------
        # Metadata sạch
        # ----------------------------------------------------

        safe_kwargs = {}

        for key, value in kwargs.items():

            if key in {
                "message",
            }:
                continue

            safe_kwargs[key] = value

        # ----------------------------------------------------
        # Kiểm tra signature
        #
        # Nếu handler có **kwargs:
        #   truyền toàn bộ metadata.
        #
        # Nếu handler chỉ nhận một số tham số:
        #   chỉ truyền những tham số hợp lệ.
        # ----------------------------------------------------

        try:

            signature = inspect.signature(
                handler
            )

            parameters = signature.parameters

            accepts_kwargs = any(
                parameter.kind
                == inspect.Parameter.VAR_KEYWORD
                for parameter in parameters.values()
            )

            if accepts_kwargs:

                return handler(
                    message,
                    **safe_kwargs,
                )

            allowed_kwargs = {}

            for key, value in safe_kwargs.items():

                parameter = parameters.get(
                    key
                )

                if parameter is None:
                    continue

                if parameter.kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                ):
                    allowed_kwargs[key] = value

            return handler(
                message,
                **allowed_kwargs,
            )

        except (TypeError, ValueError):

            # ------------------------------------------------
            # Fallback tối đa tương thích với handler cũ.
            # ------------------------------------------------

            try:
                return handler(
                    message
                )
            except Exception:
                raise

    # ========================================================
    # RESOLVE TOOL
    # ========================================================

    def _resolve_tool(
        self,
        decision: Any,
    ) -> str:

        tool = clean_text(
            get_value(
                decision,
                "tool",
                "",
            )
        ).lower()

        intent = clean_text(
            get_value(
                decision,
                "intent",
                "",
            )
        ).lower()

        aliases = {
            "browser": "web",
            "search": "web",
            "web_search": "web",
            "ollama_chat": "ollama",
            "llm": "ollama",
            "command": "action",
            "commands": "action",
        }

        tool = aliases.get(
            tool,
            tool,
        )

        if tool:
            return tool

        if intent == "action":
            return "action"

        if intent == "web":
            return "web"

        if intent in {
            "chat",
            "question",
            "conversation",
        }:
            return "ollama"

        if intent == "memory":
            return "memory"

        return ""

    # ========================================================
    # CLARIFICATION
    # ========================================================

    def _clarification_result(
        self,
        message: str,
        decision: Any,
    ) -> ExecutionResult:

        response = clean_text(
            get_value(
                decision,
                "response",
                "",
            )
        )

        if not response:
            response = (
                "Lam nói rõ hơn một chút để Minh thực hiện chính xác nhé."
            )

        return ExecutionResult(
            success=True,
            response=response,
            intent=clean_text(
                get_value(
                    decision,
                    "intent",
                    "clarification",
                )
            ),
            tool="",
            metadata={
                "clarification": True,
                "message": message,
            },
        )

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(
        self,
        message: str = "",
        decision: Any = None,
    ) -> ExecutionResult:

        message = clean_text(
            message
        )

        if decision is None:
            decision = {}

        # ----------------------------------------------------
        # Empty input
        # ----------------------------------------------------

        if not message:
            return ExecutionResult(
                success=False,
                response="",
                error="empty_message",
            )

        # ----------------------------------------------------
        # Extract decision
        # ----------------------------------------------------

        intent = clean_text(
            get_value(
                decision,
                "intent",
                "",
            )
        ).lower()

        tool = self._resolve_tool(
            decision
        )

        action = clean_text(
            get_value(
                decision,
                "action",
                "",
            )
        ).lower()

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

        needs_clarification = bool(
            get_value(
                decision,
                "needs_clarification",
                False,
            )
        )

        # ----------------------------------------------------
        # Clarification
        # ----------------------------------------------------

        if needs_clarification:

            return self._clarification_result(
                message,
                decision,
            )

        # ----------------------------------------------------
        # Special routing:
        #
        # action_web:
        # thử web trước nếu có web handler,
        # sau đó mới action.
        # ----------------------------------------------------

        if intent == "action_web":

            web_handler = self.get_handler(
                "web"
            )

            action_handler = self.get_handler(
                "action"
            )

            if web_handler:

                try:

                    raw = self._call_handler(
                        web_handler,
                        message,
                        intent=intent,
                        tool="web",
                        action=action,
                        target=target,
                        query=query,
                        reference=reference,
                        source_number=source_number,
                        decision=decision,
                    )

                    success, response, error = (
                        normalize_handler_result(
                            raw
                        )
                    )

                    if success:

                        return ExecutionResult(
                            success=True,
                            response=response,
                            intent=intent,
                            tool="web",
                            action=action,
                            target=target,
                            error=error,
                            metadata={
                                "handler": "web",
                            },
                        )

                except Exception as exc:

                    web_error = clean_text(
                        exc
                    )

                else:
                    web_error = error

            else:
                web_error = "web_handler_missing"

            if action_handler:

                try:

                    raw = self._call_handler(
                        action_handler,
                        message,
                        intent=intent,
                        tool="action",
                        action=action,
                        target=target,
                        query=query,
                        reference=reference,
                        source_number=source_number,
                        decision=decision,
                    )

                    success, response, error = (
                        normalize_handler_result(
                            raw
                        )
                    )

                    return ExecutionResult(
                        success=success,
                        response=response,
                        intent=intent,
                        tool="action",
                        action=action,
                        target=target,
                        error=error or web_error,
                        metadata={
                            "handler": "action",
                            "web_attempted": True,
                        },
                    )

                except Exception as exc:

                    return ExecutionResult(
                        success=False,
                        response="",
                        intent=intent,
                        tool="action",
                        action=action,
                        target=target,
                        error=clean_text(
                            exc
                        ),
                        metadata={
                            "handler": "action",
                            "web_attempted": True,
                        },
                    )

            return ExecutionResult(
                success=False,
                response="",
                intent=intent,
                tool="",
                action=action,
                target=target,
                error=web_error,
            )

        # ====================================================
        # NORMAL HANDLER
        # ====================================================

        handler = self.get_handler(
            tool
        )

        if handler is None:

            return ExecutionResult(
                success=False,
                response="",
                intent=intent,
                tool=tool,
                action=action,
                target=target,
                error=(
                    f"handler_missing:{tool}"
                    if tool
                    else "tool_missing"
                ),
            )

        # ----------------------------------------------------
        # Call
        # ----------------------------------------------------

        try:

            raw = self._call_handler(
                handler,
                message,
                intent=intent,
                tool=tool,
                action=action,
                target=target,
                query=query,
                reference=reference,
                source_number=source_number,
                decision=decision,
            )

        except Exception as exc:

            return ExecutionResult(
                success=False,
                response="",
                intent=intent,
                tool=tool,
                action=action,
                target=target,
                error=clean_text(
                    exc
                ),
                metadata={
                    "handler": tool,
                },
            )

        # ----------------------------------------------------
        # Normalize
        # ----------------------------------------------------

        success, response, error = (
            normalize_handler_result(
                raw
            )
        )

        return ExecutionResult(
            success=success,
            response=response,
            intent=intent,
            tool=tool,
            action=action,
            target=target,
            error=error,
            metadata={
                "handler": tool,
            },
        )

    # ========================================================
    # SHORTCUTS
    # ========================================================

    def execute_action(
        self,
        message: str = "",
        **kwargs: Any,
    ) -> ExecutionResult:

        return self.execute(
            message,
            {
                "intent": "action",
                "tool": "action",
                **kwargs,
            },
        )

    def execute_web(
        self,
        message: str = "",
        **kwargs: Any,
    ) -> ExecutionResult:

        return self.execute(
            message,
            {
                "intent": "web",
                "tool": "web",
                **kwargs,
            },
        )

    def execute_chat(
        self,
        message: str = "",
        **kwargs: Any,
    ) -> ExecutionResult:

        return self.execute(
            message,
            {
                "intent": "chat",
                "tool": "ollama",
                **kwargs,
            },
        )

    # ========================================================
    # STATUS
    # ========================================================

    def status(self) -> Dict[str, Any]:

        return {
            "handlers": sorted(
                self.handlers.keys()
            ),
            "count": len(
                self.handlers
            ),
        }

    # ========================================================
    # DESCRIBE
    # ========================================================

    def describe(self) -> Dict[str, Any]:

        result = {}

        for name, handler in self.handlers.items():

            try:
                signature = str(
                    inspect.signature(
                        handler
                    )
                )
            except Exception:
                signature = "unknown"

            result[name] = {
                "callable": callable(
                    handler
                ),
                "signature": signature,
            }

        return result


# ============================================================
# FACTORIES
# ============================================================

def create_controller(
    handlers: Optional[
        Dict[str, Callable]
    ] = None,
) -> ExecutionController:

    return ExecutionController(
        handlers=handlers
    )


def build_execution_controller(
    handlers: Optional[
        Dict[str, Callable]
    ] = None,
) -> ExecutionController:

    return ExecutionController(
        handlers=handlers
    )


Controller = ExecutionController


# ============================================================
# MODULE LEVEL EXECUTE
# ============================================================

def execute(
    message: str = "",
    decision: Any = None,
    handlers: Optional[
        Dict[str, Callable]
    ] = None,
) -> ExecutionResult:

    controller = ExecutionController(
        handlers=handlers
    )

    return controller.execute(
        message,
        decision,
    )


# ============================================================
# SELF CHECK
# ============================================================

def self_check() -> Dict[str, bool]:

    checks: Dict[str, bool] = {}

    # --------------------------------------------------------
    # Fake handlers
    # --------------------------------------------------------

    def fake_action(
        message="",
        **kwargs,
    ):

        return {
            "success": True,
            "response": "ACTION_OK",
        }

    def fake_web(
        message="",
        **kwargs,
    ):

        return {
            "success": True,
            "response": "WEB_OK",
        }

    def fake_chat(
        message="",
        **kwargs,
    ):

        return {
            "success": True,
            "response": "CHAT_OK",
        }

    controller = ExecutionController(
        handlers={
            "action": fake_action,
            "web": fake_web,
            "ollama": fake_chat,
            "chat": fake_chat,
        }
    )

    # --------------------------------------------------------
    # Action
    # --------------------------------------------------------

    try:

        result = controller.execute(
            "mở Google",
            {
                "intent": "action",
                "tool": "action",
                "action": "open",
                "target": "google",
            },
        )

        checks["action"] = (
            result.success
            and result.response == "ACTION_OK"
            and result.tool == "action"
        )

    except Exception:
        checks["action"] = False

    # --------------------------------------------------------
    # Web
    # --------------------------------------------------------

    try:

        result = controller.execute(
            "tìm trên web giá iPhone",
            {
                "intent": "web",
                "tool": "web",
                "action": "search",
                "query": "giá iPhone",
            },
        )

        checks["web"] = (
            result.success
            and result.response == "WEB_OK"
            and result.tool == "web"
        )

    except Exception:
        checks["web"] = False

    # --------------------------------------------------------
    # Chat
    # --------------------------------------------------------

    try:

        result = controller.execute(
            "xin chào",
            {
                "intent": "chat",
                "tool": "ollama",
            },
        )

        checks["chat"] = (
            result.success
            and result.response == "CHAT_OK"
            and result.tool == "ollama"
        )

    except Exception:
        checks["chat"] = False

    # --------------------------------------------------------
    # Empty
    # --------------------------------------------------------

    try:

        result = controller.execute(
            "",
            {},
        )

        checks["empty"] = (
            result.success is False
            and result.response == ""
        )

    except Exception:
        checks["empty"] = False

    # --------------------------------------------------------
    # Old-style handler
    # --------------------------------------------------------

    def old_handler(message=""):

        return "OLD_HANDLER_OK"

    old_controller = ExecutionController(
        handlers={
            "action": old_handler,
        }
    )

    try:

        result = old_controller.execute(
            "test",
            {
                "intent": "action",
                "tool": "action",
            },
        )

        checks["old_handler"] = (
            result.success
            and result.response
            == "OLD_HANDLER_OK"
        )

    except Exception:
        checks["old_handler"] = False

    return checks


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "MINH MINI — EXECUTION CONTROLLER FINAL"
    )

    checks = self_check()

    for name, passed in checks.items():

        print(
            f"[{'PASS' if passed else 'FAIL'}] {name}"
        )

    print()

    if all(checks.values()):
        print(
            "SELF CHECK: PASS"
        )
    else:
        print(
            "SELF CHECK: FAIL"
        )