from pathlib import Path
import ast
import shutil

MAIN = Path("main.py")
BACKUP = Path("main_p45_execution_verify_before.py")

print("=== P4-5 EXECUTION -> VERIFY PATCH ===")

# ============================================================
# READ + AST CHECK
# ============================================================

source = MAIN.read_text(encoding="utf-8")
tree = ast.parse(source)

print("ORIGINAL AST: PASS")

# ============================================================
# FIND MinhMiniCore
# ============================================================

core = None

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "MinhMiniCore":
        core = node
        break

if core is None:
    raise RuntimeError("Không tìm thấy class MinhMiniCore")

print("MinhMiniCore: FOUND")

# ============================================================
# FIND __init__
# ============================================================

init_node = None
process_node = None

for node in core.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "__init__":
            init_node = node
        elif node.name == "process":
            process_node = node

if init_node is None:
    raise RuntimeError("Không tìm thấy MinhMiniCore.__init__()")

if process_node is None:
    raise RuntimeError("Không tìm thấy MinhMiniCore.process()")

print(
    f"__init__(): "
    f"{init_node.lineno}-{getattr(init_node, 'end_lineno', '?')}"
)

print(
    f"process(): "
    f"{process_node.lineno}-{getattr(process_node, 'end_lineno', '?')}"
)

# ============================================================
# EXISTING CHECK
# ============================================================

required_existing = [
    "# EXECUTION_CONTRACT_P44_BUILD",
    "# EXECUTION_CONTRACT_P44_GATE",
    "self.last_execution_contract",
    "self.execute_decision(",
]

for marker in required_existing:
    if marker not in source:
        raise RuntimeError(
            "Thiếu foundation bắt buộc: " + marker
        )

print("P4-4 FOUNDATION: PASS")

# ============================================================
# PREVENT DUPLICATE PATCH
# ============================================================

if "# P45_EXECUTION_VERIFY_INIT" in source:
    raise RuntimeError(
        "P4-5 VERIFY đã tồn tại. Không patch lần nữa."
    )

# ============================================================
# BACKUP
# ============================================================

shutil.copy2(MAIN, BACKUP)
print("BACKUP: PASS")
print("BACKUP FILE:", BACKUP.name)

# ============================================================
# PATCH 1 — INIT VERIFY STATE
# ============================================================

init_marker = "        # EXECUTION_CONTRACT_P44_LAST_RESULT_INIT\n"

init_insert = """        # EXECUTION_CONTRACT_P44_LAST_RESULT_INIT
        self.last_execution_contract = None

        # P45_EXECUTION_VERIFY_INIT
        self.last_execution_verification = None
"""

if init_marker not in source:
    raise RuntimeError(
        "Không tìm thấy EXECUTION_CONTRACT_P44_LAST_RESULT_INIT"
    )

source = source.replace(
    init_marker,
    init_insert,
    1,
)

print("VERIFY INIT: PASS")

# ============================================================
# PATCH 2 — VERIFY METHOD
# ============================================================

verify_method = r'''
    # --------------------------------------------------------
    # P4-5 EXECUTION RESULT VERIFIER
    # --------------------------------------------------------

    def verify_execution_result(
        self,
        message: str,
        decision: Any,
        execution_result: Any,
        answer: str,
    ) -> dict:
        """
        P4-5 deterministic execution verification.

        Không thực thi lại action.
        Không gọi Ollama.
        Chỉ kiểm tra execution result đã có cấu trúc
        thành công/thất bại hợp lệ hay chưa.
        """

        intent = clean_text(
            get_decision_value(
                decision,
                "intent",
                "",
            )
        )

        success = get_decision_value(
            execution_result,
            "success",
            None,
        )

        error = get_decision_value(
            execution_result,
            "error",
            "",
        )

        tool = clean_text(
            get_decision_value(
                execution_result,
                "tool",
                "",
            )
        )

        checks = []

        # ----------------------------------------------------
        # Basic result existence
        # ----------------------------------------------------

        if execution_result is None:
            checks.append("missing_execution_result")

        # ----------------------------------------------------
        # Success must be explicit
        # ----------------------------------------------------

        if success is True:
            checks.append("success_true")
        elif success is False:
            checks.append("success_false")
        else:
            checks.append("success_unknown")

        # ----------------------------------------------------
        # Answer check
        # ----------------------------------------------------

        answer_ok = bool(
            isinstance(answer, str)
            and answer.strip()
        )

        if answer_ok:
            checks.append("answer_present")
        else:
            checks.append("answer_missing")

        # ----------------------------------------------------
        # Error consistency
        # ----------------------------------------------------

        if success is False and error:
            checks.append("error_present")
        elif success is False and not error:
            checks.append("error_missing")

        # ----------------------------------------------------
        # Tool consistency
        # ----------------------------------------------------

        if intent in {
            "action",
            "web",
            "memory",
            "time",
            "date",
        }:
            if tool:
                checks.append("tool_present")
            else:
                checks.append("tool_missing")

        # ----------------------------------------------------
        # PASS / FAIL
        # ----------------------------------------------------

        if execution_result is None:
            verified = False
            status = "fail"

        elif success is False:
            verified = False
            status = "fail"

        elif success is not True:
            verified = False
            status = "fail"

        elif not answer_ok:
            verified = False
            status = "fail"

        elif (
            intent in {
                "action",
                "web",
                "memory",
                "time",
                "date",
            }
            and not tool
        ):
            verified = False
            status = "fail"

        else:
            verified = True
            status = "pass"

        return {
            "verified": verified,
            "status": status,
            "success": success,
            "tool": tool,
            "intent": intent,
            "answer_present": answer_ok,
            "error": error,
            "checks": checks,
            "message": message,
        }

'''

# Insert before execute_decision().
execute_source = ast.get_source_segment(
    source,
    process_node,
)

# Reparse because init changed.
tree = ast.parse(source)

core = None
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "MinhMiniCore":
        core = node
        break

execute_node = None

for node in core.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "execute_decision":
            execute_node = node
            break

if execute_node is None:
    raise RuntimeError(
        "Không tìm thấy execute_decision()"
    )

lines = source.splitlines(keepends=True)

insert_index = execute_node.lineno - 1

lines.insert(
    insert_index,
    verify_method,
)

source = "".join(lines)

print("VERIFY METHOD: PASS")

# ============================================================
# PATCH 3 — VERIFY AFTER EXECUTION
# ============================================================

verify_anchor = """        # GOAL_MANAGER_V6_RESULT
"""

if verify_anchor not in source:
    raise RuntimeError(
        "Không tìm thấy GOAL_MANAGER_V6_RESULT"
    )

verify_block = """        # P45_EXECUTION_VERIFY
        verification = None
        try:
            verifier = getattr(
                self,
                "verify_execution_result",
                None,
            )

            if callable(verifier):
                verification = verifier(
                    completed,
                    decision,
                    execution_result,
                    answer,
                )

            self.last_execution_verification = verification

        except Exception as exc:
            self.last_execution_verification = None
            verification = {
                "verified": False,
                "status": "fail",
                "success": get_decision_value(
                    execution_result,
                    "success",
                    None,
                ),
                "error": repr(exc),
                "checks": [
                    "verification_exception",
                ],
            }

            log(
                "EXECUTION VERIFY ERROR: "
                + traceback.format_exc()
            )

        # GOAL_MANAGER_V6_RESULT
"""

source = source.replace(
    verify_anchor,
    verify_block,
    1,
)

print("VERIFY FLOW: PASS")

# ============================================================
# PATCH 4 — CONTEXT / HISTORY VERIFICATION METADATA
# ============================================================

history_anchor = """                "target": get_decision_value(
                    decision,
                    "target",
                    "",
                ),
            },
"""

history_replacement = """                "target": get_decision_value(
                    decision,
                    "target",
                    "",
                ),
                "verified": (
                    get_decision_value(
                        verification,
                        "verified",
                        False,
                    )
                    if verification is not None
                    else False
                ),
                "verification_status": (
                    get_decision_value(
                        verification,
                        "status",
                        "fail",
                    )
                    if verification is not None
                    else "fail"
                ),
            },
"""

if history_anchor not in source:
    raise RuntimeError(
        "Không tìm thấy HISTORY target anchor"
    )

source = source.replace(
    history_anchor,
    history_replacement,
    1,
)

print("HISTORY VERIFY METADATA: PASS")

# ============================================================
# FINAL AST CHECK
# ============================================================

ast.parse(source)
print("FINAL AST: PASS")

# ============================================================
# WRITE
# ============================================================

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("CHECK: P45_EXECUTION_VERIFY_INIT = PASS")
print("CHECK: verify_execution_result() = PASS")
print("CHECK: P45_EXECUTION_VERIFY = PASS")
print("CHECK: last_execution_verification = PASS")
print("CHECK: verification metadata = PASS")
print("PATCH STATUS: PASS")
print("MAIN.PY UPDATED")
