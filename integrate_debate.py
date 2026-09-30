from pathlib import Path

path = Path(r"C:\Users\Admin\MINH_MINI\app\main.py")

source = path.read_text(encoding="utf-8")

# ============================================================
# SAFETY CHECK
# ============================================================

if "# DEBATE_1_1_GATE" in source:
    raise RuntimeError(
        "DEBATE da duoc tich hop vao main.py. Khong ghi lai."
    )

original_source = source


# ============================================================
# 1. IMPORT DEBATE
# ============================================================

import_marker = 'chat_module = safe_import("chat")'

if import_marker not in source:
    raise RuntimeError(
        "Khong tim thay chat_module import marker."
    )

source = source.replace(
    import_marker,
    import_marker + '\ndebate_module = safe_import("debate")',
    1,
)


# ============================================================
# 2. INIT DEBATE ENGINE
# ============================================================

init_marker = """        self.turn_count = len(
            HISTORY
        )
"""

if init_marker not in source:
    raise RuntimeError(
        "Khong tim thay self.turn_count init."
    )

init_block = """        self.turn_count = len(
            HISTORY
        )

        # DEBATE_1_1_INIT
        # /debate la technical decision mode.
        # Khong phai execution handler.
        try:
            create_debate = getattr(
                debate_module,
                "get_debate",
                None,
            )

            self.debate = (
                create_debate()
                if callable(create_debate)
                else None
            )

        except Exception as exc:
            self.debate = None
            log(
                "DEBATE INIT ERROR: "
                + repr(exc)
            )
"""

source = source.replace(
    init_marker,
    init_block,
    1,
)


# ============================================================
# 3. STATUS
# ============================================================

status_marker = '''            "history_items": len(HISTORY),
        }'''

if status_marker not in source:
    raise RuntimeError(
        "Khong tim thay status marker."
    )

status_block = '''            "history_items": len(HISTORY),
            "debate": (
                self.debate is not None
            ),
            "debate_mode": (
                "analysis_only"
                if self.debate is not None
                else "unavailable"
            ),
            "debate_execution": False,
        }'''

source = source.replace(
    status_marker,
    status_block,
    1,
)


# ============================================================
# 4. PROCESS_DEBATE METHOD
# ============================================================

normalize_marker = """    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------
"""

if normalize_marker not in source:
    raise RuntimeError(
        "Khong tim thay NORMALIZE marker."
    )

debate_method = """    # --------------------------------------------------------
    # DEBATE
    # --------------------------------------------------------

    def process_debate(
        self,
        message: str,
    ) -> str | None:

        if self.debate is None:
            return None

        try:
            detector = getattr(
                self.debate,
                "is_debate_command",
                None,
            )

            if not callable(detector):
                return None

            if not detector(message):
                return None

            debate_function = getattr(
                self.debate,
                "debate",
                None,
            )

            if not callable(debate_function):
                log(
                    "DEBATE ERROR: debate() unavailable"
                )
                return (
                    "DEBATE chua san sang."
                )

            result = debate_function(
                message
            )

            if isinstance(result, str):
                answer = clean_text(result)

            else:
                formatter = getattr(
                    self.debate,
                    "format_result",
                    None,
                )

                if callable(formatter):
                    answer = clean_text(
                        formatter(result)
                    )
                else:
                    answer = clean_text(
                        str(result)
                    )

            if not answer:
                answer = (
                    "Minh chua tao duoc phan tich "
                    "DEBATE cho yeu cau nay."
                )

            # IMPORTANT:
            # DEBATE only analyzes.
            # It does NOT execute Action/Web/Controller.
            return answer

        except Exception as exc:
            log(
                "DEBATE ERROR: "
                + traceback.format_exc()
            )

            return (
                "Minh gap loi khi phan tich /debate: "
                + clean_text(str(exc))
            )

"""

source = source.replace(
    normalize_marker,
    debate_method + normalize_marker,
    1,
)


# ============================================================
# 5. /DEBATE GATE
# ============================================================

process_start = source.find("    def process(\n")

if process_start < 0:
    raise RuntimeError(
        "Khong tim thay MinhMiniCore.process()."
    )

turn_marker = "        self.turn_count += 1"

turn_pos = source.find(
    turn_marker,
    process_start,
)

if turn_pos < 0:
    raise RuntimeError(
        "Khong tim thay turn_count trong process()."
    )

gate = """        # DEBATE_1_1_GATE
        # Bat /debate truoc COMMAND COMPLETION va BRAIN.
        # Tuyet doi khong dua DEBATE vao ExecutionController.
        self.last_execution_verification = None

        debate_detector = getattr(
            self.debate,
            "is_debate_command",
            None,
        ) if self.debate is not None else None

        if callable(debate_detector):
            try:
                if debate_detector(original):

                    self.turn_count += 1

                    log(
                        f"USER: {original}"
                    )

                    add_history(
                        "user",
                        original,
                    )

                    answer = self.process_debate(
                        original
                    )

                    if answer is None:
                        answer = (
                            "DEBATE chua san sang."
                        )

                    add_history(
                        "assistant",
                        answer,
                        {
                            "intent": "debate",
                            "tool": "debate",
                            "execution_blocked": True,
                            "execution": False,
                        },
                    )

                    update_context(
                        original,
                        answer,
                        {
                            "intent": "debate",
                            "tool": "debate",
                            "execution_blocked": True,
                        },
                    )

                    log(
                        f"ASSISTANT: {answer}"
                    )

                    return answer

            except Exception as exc:
                log(
                    "DEBATE GATE ERROR: "
                    + traceback.format_exc()
                )

        self.turn_count += 1
"""

source = (
    source[:turn_pos]
    + gate
    + source[turn_pos + len(turn_marker):]
)


# ============================================================
# 6. PUBLIC DEBATE API
# ============================================================

chat_marker = """def chat(
    message: str,
) -> str:

    return process(
        message
    )


def status() -> dict[str, Any]:
"""

if chat_marker not in source:
    raise RuntimeError(
        "Khong tim thay public chat/status marker."
    )

public_api = """def chat(
    message: str,
) -> str:

    return process(
        message
    )


def debate(
    message: str,
) -> str:

    result = MINH.process_debate(
        message
    )

    return result or "DEBATE chua san sang."


def status() -> dict[str, Any]:
"""

source = source.replace(
    chat_marker,
    public_api,
    1,
)


# ============================================================
# FINAL SAFETY CHECKS BEFORE WRITE
# ============================================================

required_markers = {
    "debate_import": 'debate_module = safe_import("debate")',
    "debate_init": "# DEBATE_1_1_INIT",
    "debate_method": "def process_debate(",
    "debate_gate": "# DEBATE_1_1_GATE",
    "debate_api": "def debate(",
    "p45": "# P45_EXECUTION_VERIFY_INIT",
    "verify_function": "def verify_execution_result(",
    "execute_function": "def execute_decision(",
}

for name, marker in required_markers.items():
    if marker not in source:
        raise RuntimeError(
            "SAFETY CHECK FAILED: missing "
            + name
            + " -> "
            + marker
        )

# DEBATE must NOT become an execution handler.
if '"debate": handle_' in source:
    raise RuntimeError(
        "SAFETY CHECK FAILED: DEBATE dang nam trong handler map."
    )

# Must still contain the protected P4-5 lifecycle.
if "P45_EXECUTION_VERIFY_INIT" not in source:
    raise RuntimeError(
        "SAFETY CHECK FAILED: P4-5 init missing."
    )

# ============================================================
# WRITE ONLY AFTER ALL CHECKS PASS
# ============================================================

path.write_text(
    source,
    encoding="utf-8",
)

print()
print("============================================================")
print("DEBATE INTEGRATION COMPLETE")
print("============================================================")
print("FILE              :", path)
print("DEBATE IMPORT     : PASS")
print("DEBATE INIT       : PASS")
print("DEBATE METHOD     : PASS")
print("DEBATE GATE       : PASS")
print("DEBATE PUBLIC API : PASS")
print("P4-5 PRESERVED    : PASS")
print("EXECUTION HANDLER : NOT ADDED")
print("============================================================")
