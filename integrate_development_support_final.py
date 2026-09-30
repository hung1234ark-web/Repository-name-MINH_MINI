from pathlib import Path
import shutil
import py_compile
import importlib
import sys
import re


APP = Path(__file__).resolve().parent
MAIN = APP / "main.py"
BACKUP = APP / "main.py.before_development_support_final"


def fail(msg):
    print("")
    print("============================================================")
    print("DEVELOPMENT SUPPORT INTEGRATION: FAIL")
    print("============================================================")
    print(msg)
    sys.exit(1)


if not MAIN.exists():
    fail(f"Khong tim thay {MAIN}")


source = MAIN.read_text(encoding="utf-8")


# ============================================================
# SAFETY
# ============================================================

if "DEVELOPMENT_SUPPORT_INTEGRATED" in source:
    fail("Development Support da ton tai trong main.py.")

required = [
    "DEBATE_1_1_INIT",
    "DEBATE_1_1_GATE",
    "def process_debate(",
    "def process(",
    '"debate_execution": False',
    "verify_execution_result",
    "ExecutionController",
]

for item in required:
    if item not in source:
        fail("Thieu cau truc bat buoc: " + item)


# ============================================================
# BACKUP
# ============================================================

shutil.copy2(MAIN, BACKUP)
print("BACKUP CREATED:", BACKUP)


# ============================================================
# 1. FIND CLASS INIT / DEBATE INIT
# ============================================================

debate_init_pos = source.find("# DEBATE_1_1_INIT")

if debate_init_pos < 0:
    fail("Khong tim thay DEBATE_1_1_INIT.")


development_init = """# DEVELOPMENT_SUPPORT_INTEGRATED
        # Development Support la lop quan ly qua trinh phat trien.
        # Khong phai execution handler.
        # Khong tu dong thuc thi task.
        try:
            import development_support as development_support_module

            create_development_support = getattr(
                development_support_module,
                "get_support",
                None,
            )

            self.development_support = (
                create_development_support()
                if callable(create_development_support)
                else None
            )

        except Exception as exc:
            self.development_support = None
            log(
                "DEVELOPMENT SUPPORT INIT ERROR: "
                + repr(exc)
            )

        """


source = (
    source[:debate_init_pos]
    + development_init
    + source[debate_init_pos:]
)


# ============================================================
# 2. FIND STATUS METHOD
#
# Khong dua vao indentation cua dict.
# Tim def status -> ket thuc truoc method tiep theo.
# ============================================================

status_match = re.search(
    r"(?m)^    def status\(\s*\n",
    source,
)

if not status_match:
    fail(
        "Khong tim thay class method def status()."
    )


status_start = status_match.start()

next_method = re.search(
    r"(?m)^    def [A-Za-z_][A-Za-z0-9_]*\(",
    source[status_match.end():],
)

if not next_method:
    fail(
        "Khong tim thay method tiep theo sau status()."
    )


status_end = (
    status_match.end()
    + next_method.start()
)


status_block = source[
    status_start:status_end
]


# ------------------------------------------------------------
# Tìm dòng chứa debate_execution trong status.
# ------------------------------------------------------------

debate_exec_match = re.search(
    r'(?m)^([ \t]*)"debate_execution": False,\s*$',
    status_block,
)

if not debate_exec_match:
    fail(
        "Tim thay status() nhung khong tim duoc "
        '"debate_execution": False.'
    )


indent = debate_exec_match.group(1)


# ------------------------------------------------------------
# Chèn ngay trước debate block.
# ------------------------------------------------------------

status_insert = (
    indent + '"development_support": (\n'
    + indent + '    self.development_support is not None\n'
    + indent + '),\n'
    + indent + '"development_support_mode": (\n'
    + indent + '    "development_management"\n'
    + indent + '    if self.development_support is not None\n'
    + indent + '    else "unavailable"\n'
    + indent + '),\n'
    + indent + '"development_support_execution": False,\n'
)


absolute_status_pos = (
    status_start
    + debate_exec_match.start()
)


source = (
    source[:absolute_status_pos]
    + status_insert
    + source[absolute_status_pos:]
)


# ============================================================
# 3. PUBLIC API
# ============================================================

api_anchor = re.search(
    r"(?m)^    def process_debate\(",
    source,
)

if not api_anchor:
    fail(
        "Khong tim thay class method process_debate()."
    )


api = """    # --------------------------------------------------------
    # DEVELOPMENT SUPPORT PUBLIC API
    # --------------------------------------------------------

    def development_status(
        self,
    ) -> dict[str, Any]:
        \"\"\"
        Trang thai Development Support.

        Chi quan ly development task/contract/context/
        change request.

        Khong thuc thi task.
        \"\"\"
        support = getattr(
            self,
            "development_support",
            None,
        )

        if support is None:
            return {
                "available": False,
                "execution": False,
            }

        try:
            method = getattr(
                support,
                "status",
                None,
            )

            if callable(method):
                result = method()

                if isinstance(result, dict):
                    result = dict(result)
                    result.setdefault(
                        "available",
                        True,
                    )
                    result.setdefault(
                        "execution",
                        False,
                    )
                    return result

                return {
                    "available": True,
                    "status": result,
                    "execution": False,
                }

        except Exception:
            log(
                "DEVELOPMENT SUPPORT STATUS ERROR: "
                + traceback.format_exc()
            )

        return {
            "available": True,
            "execution": False,
        }


    def development_create_task(
        self,
        *args,
        **kwargs,
    ):
        \"\"\"Tao Development Contract, khong thuc thi task.\"\"\"
        support = getattr(
            self,
            "development_support",
            None,
        )

        if support is None:
            return None

        method = getattr(
            support,
            "create_contract",
            None,
        )

        if not callable(method):
            return None

        return method(
            *args,
            **kwargs,
        )


    def development_get_status(
        self,
        *args,
        **kwargs,
    ):
        \"\"\"Lay Development Support status.\"\"\"
        return self.development_status()


    def development_change_request(
        self,
        *args,
        **kwargs,
    ):
        \"\"\"
        Tao Change Request.

        Khong tu dong approve.
        \"\"\"
        support = getattr(
            self,
            "development_support",
            None,
        )

        if support is None:
            return None

        method = getattr(
            support,
            "request_change",
            None,
        )

        if not callable(method):
            return None

        return method(
            *args,
            **kwargs,
        )


"""


source = (
    source[:api_anchor.start()]
    + api
    + source[api_anchor.start():]
)


# ============================================================
# WRITE
# ============================================================

MAIN.write_text(
    source,
    encoding="utf-8",
)


# ============================================================
# COMPILE
# ============================================================

try:
    py_compile.compile(
        str(MAIN),
        doraise=True,
    )
except Exception as exc:
    print("")
    print("COMPILE: FAIL")
    print(repr(exc))
    print("ROLLBACK...")

    shutil.copy2(BACKUP, MAIN)

    py_compile.compile(
        str(MAIN),
        doraise=True,
    )

    print("ROLLBACK: PASS")
    sys.exit(1)

print("COMPILE: PASS")


# ============================================================
# IMPORT
# ============================================================

try:
    if "main" in sys.modules:
        del sys.modules["main"]

    module = importlib.import_module("main")
    MINH = getattr(module, "MINH")

except Exception as exc:
    print("")
    print("IMPORT: FAIL")
    print(repr(exc))
    print("ROLLBACK...")

    shutil.copy2(BACKUP, MAIN)

    py_compile.compile(
        str(MAIN),
        doraise=True,
    )

    print("ROLLBACK: PASS")
    sys.exit(1)

print("IMPORT: PASS")


# ============================================================
# DEVELOPMENT SUPPORT RUNTIME
# ============================================================

try:
    status = MINH.status()

    if status.get("development_support") is not True:
        raise RuntimeError(
            "development_support != True"
        )

    if status.get("development_support_mode") != (
        "development_management"
    ):
        raise RuntimeError(
            "development_support_mode sai"
        )

    if status.get(
        "development_support_execution"
    ) is not False:
        raise RuntimeError(
            "development_support_execution phai False"
        )

    for name in (
        "development_create_task",
        "development_get_status",
        "development_change_request",
    ):
        if not callable(
            getattr(MINH, name, None)
        ):
            raise RuntimeError(
                name + " khong callable"
            )

except Exception as exc:
    print("")
    print("DEVELOPMENT SUPPORT RUNTIME: FAIL")
    print(repr(exc))
    print("ROLLBACK...")

    shutil.copy2(BACKUP, MAIN)

    py_compile.compile(
        str(MAIN),
        doraise=True,
    )

    print("ROLLBACK: PASS")
    sys.exit(1)

print("DEVELOPMENT SUPPORT RUNTIME: PASS")


# ============================================================
# DEBATE REGRESSION
# ============================================================

try:
    answer = MINH.process(
        "/debate Có nên thêm một AI mới vào MINH MINI không?"
    )

    if not answer:
        raise RuntimeError(
            "DEBATE khong tra answer"
        )

    s = MINH.status()

    if s.get("debate") is not True:
        raise RuntimeError(
            "DEBATE khong True"
        )

    if s.get("debate_mode") != "analysis_only":
        raise RuntimeError(
            "DEBATE mode sai"
        )

    if s.get("debate_execution") is not False:
        raise RuntimeError(
            "DEBATE execution sai"
        )

    if getattr(
        MINH,
        "last_execution_verification",
        None,
    ) is not None:
        raise RuntimeError(
            "DEBATE da cham vao P4-5"
        )

except Exception as exc:
    print("")
    print("DEBATE REGRESSION: FAIL")
    print(repr(exc))
    print("ROLLBACK...")

    shutil.copy2(BACKUP, MAIN)

    py_compile.compile(
        str(MAIN),
        doraise=True,
    )

    print("ROLLBACK: PASS")
    sys.exit(1)

print("DEBATE REGRESSION: PASS")


# ============================================================
# FINAL
# ============================================================

print("")
print("============================================================")
print("DEVELOPMENT SUPPORT INTEGRATION COMPLETE")
print("============================================================")
print("FILE                 :", MAIN)
print("BACKUP               :", BACKUP)
print("COMPILE              : PASS")
print("IMPORT               : PASS")
print("INIT                 : PASS")
print("STATUS               : PASS")
print("TASK API             : PASS")
print("CHANGE REQUEST API   : PASS")
print("DEBATE               : PRESERVED")
print("DEBATE REGRESSION    : PASS")
print("P4-5                 : PRESERVED")
print("EXECUTION CONTROLLER : PRESERVED")
print("EXECUTION CONTRACT   : PRESERVED")
print("AUTO EXECUTION       : NOT ADDED")
print("============================================================")
