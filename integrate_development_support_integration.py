from pathlib import Path
import shutil
import py_compile
import importlib
import sys


APP = Path(__file__).resolve().parent
MAIN = APP / "main.py"
BACKUP = APP / "main.py.before_development_support_integration"


def rollback():
    shutil.copy2(BACKUP, MAIN)
    try:
        py_compile.compile(
            str(MAIN),
            doraise=True,
        )
        print("ROLLBACK: PASS")
    except Exception as exc:
        print("ROLLBACK: FAIL")
        print(repr(exc))


def fail(message, rollback_now=True):
    print("")
    print("=" * 60)
    print("DEVELOPMENT SUPPORT INTEGRATION: FAIL")
    print("=" * 60)
    print(message)

    if rollback_now:
        print("")
        print("ROLLBACK...")
        rollback()

    sys.exit(1)


if not MAIN.exists():
    fail(
        "Khong tim thay main.py.",
        False,
    )


source = MAIN.read_text(
    encoding="utf-8",
)


# ============================================================
# SAFETY CHECK
# ============================================================

if "DEVELOPMENT_SUPPORT_INTEGRATED" in source:
    fail(
        "Development Support da co dau hieu tich hop. "
        "Khong patch lan hai."
    )


required = [
    "# DEBATE_1_1_INIT",
    "def status(self) -> dict[str, Any]:",
    "def process_debate(",
    '"debate_execution": False,',
    "verify_execution_result",
]


for item in required:
    if item not in source:
        fail(
            "Thieu cau truc bat buoc: "
            + repr(item)
        )


# ============================================================
# BACKUP
# ============================================================

shutil.copy2(
    MAIN,
    BACKUP,
)

print(
    "BACKUP CREATED:",
    BACKUP,
)


# ============================================================
# 1. DEVELOPMENT SUPPORT INIT
# ============================================================

marker = "# DEBATE_1_1_INIT"

marker_pos = source.find(marker)

if marker_pos < 0:
    fail(
        "Khong tim thay DEBATE_1_1_INIT."
    )


line_start = source.rfind(
    "\n",
    0,
    marker_pos,
) + 1


marker_line = source[
    line_start:
    source.find(
        "\n",
        line_start,
    )
]


init_indent = marker_line[
    :len(marker_line)
    - len(marker_line.lstrip())
]


development_init = (
    init_indent
    + "# DEVELOPMENT_SUPPORT_INTEGRATED\n"
    + init_indent
    + "# Development Support = development-management layer.\n"
    + init_indent
    + "# Khong phai execution handler.\n"
    + init_indent
    + "# Khong tu dong thuc thi task.\n"
    + init_indent
    + "try:\n"
    + init_indent
    + "    import development_support as development_support_module\n"
    + "\n"
    + init_indent
    + "    create_development_support = getattr(\n"
    + init_indent
    + "        development_support_module,\n"
    + init_indent
    + '        "get_support",\n'
    + init_indent
    + "        None,\n"
    + init_indent
    + "    )\n"
    + "\n"
    + init_indent
    + "    self.development_support = (\n"
    + init_indent
    + "        create_development_support()\n"
    + init_indent
    + "        if callable(create_development_support)\n"
    + init_indent
    + "        else None\n"
    + init_indent
    + "    )\n"
    + "\n"
    + init_indent
    + "except Exception as exc:\n"
    + init_indent
    + "    self.development_support = None\n"
    + init_indent
    + "    log(\n"
    + init_indent
    + '        "DEVELOPMENT SUPPORT INIT ERROR: "\n'
    + init_indent
    + "        + repr(exc)\n"
    + init_indent
    + "    )\n"
    + "\n"
)


source = (
    source[:line_start]
    + development_init
    + source[line_start:]
)


# ============================================================
# 2. STATUS BLOCK
# ============================================================

debate_execution = '"debate_execution": False,'

debate_exec_pos = source.find(
    debate_execution,
)

if debate_exec_pos < 0:
    fail(
        'Khong tim thay "debate_execution": False.'
    )


status_line_start = source.rfind(
    "\n",
    0,
    debate_exec_pos,
) + 1


status_line_end = source.find(
    "\n",
    debate_exec_pos,
)

if status_line_end < 0:
    status_line_end = len(source)


status_line = source[
    status_line_start:
    status_line_end
]


status_indent = status_line[
    :len(status_line)
    - len(status_line.lstrip())
]


status_insert = (
    status_indent
    + '"development_support": (\n'
    + status_indent
    + "    self.development_support is not None\n"
    + status_indent
    + "),\n"
    + status_indent
    + '"development_support_mode": (\n'
    + status_indent
    + '    "development_management"\n'
    + status_indent
    + "    if self.development_support is not None\n"
    + status_indent
    + '    else "unavailable"\n'
    + status_indent
    + "),\n"
    + status_indent
    + '"development_support_execution": False,\n'
)


source = (
    source[:debate_exec_pos]
    + status_insert
    + source[debate_exec_pos:]
)


# ============================================================
# 3. PUBLIC DEVELOPMENT SUPPORT METHODS
# ============================================================

process_marker = "    def process_debate("

process_pos = source.find(
    process_marker,
)

if process_pos < 0:
    fail(
        "Khong tim thay class process_debate()."
    )


method_indent = "    "


api = (
    method_indent
    + "# --------------------------------------------------------\n"
    + method_indent
    + "# DEVELOPMENT SUPPORT\n"
    + method_indent
    + "# --------------------------------------------------------\n"
    + "\n"
    + method_indent
    + "def development_status(\n"
    + method_indent
    + "    self,\n"
    + method_indent
    + ") -> dict[str, Any]:\n"
    + method_indent
    + '    """Tra ve trang thai Development Support."""\n'
    + method_indent
    + "    support = getattr(\n"
    + method_indent
    + "        self,\n"
    + method_indent
    + '        "development_support",\n'
    + method_indent
    + "        None,\n"
    + method_indent
    + "    )\n"
    + "\n"
    + method_indent
    + "    if support is None:\n"
    + method_indent
    + "        return {\n"
    + method_indent
    + '            "available": False,\n'
    + method_indent
    + '            "execution": False,\n'
    + method_indent
    + "        }\n"
    + "\n"
    + method_indent
    + "    try:\n"
    + method_indent
    + "        method = getattr(\n"
    + method_indent
    + "            support,\n"
    + method_indent
    + '            "status",\n'
    + method_indent
    + "            None,\n"
    + method_indent
    + "        )\n"
    + "\n"
    + method_indent
    + "        if callable(method):\n"
    + method_indent
    + "            result = method()\n"
    + "\n"
    + method_indent
    + "            if isinstance(result, dict):\n"
    + method_indent
    + "                result = dict(result)\n"
    + method_indent
    + "                result.setdefault(\n"
    + method_indent
    + '                    "available",\n'
    + method_indent
    + "                    True,\n"
    + method_indent
    + "                )\n"
    + method_indent
    + "                result.setdefault(\n"
    + method_indent
    + '                    "execution",\n'
    + method_indent
    + "                    False,\n"
    + method_indent
    + "                )\n"
    + method_indent
    + "                return result\n"
    + "\n"
    + method_indent
    + "            return {\n"
    + method_indent
    + '                "available": True,\n'
    + method_indent
    + '                "status": result,\n'
    + method_indent
    + '                "execution": False,\n'
    + method_indent
    + "            }\n"
    + "\n"
    + method_indent
    + "    except Exception as exc:\n"
    + method_indent
    + "        log(\n"
    + method_indent
    + '            "DEVELOPMENT SUPPORT STATUS ERROR: "\n'
    + method_indent
    + "            + repr(exc)\n"
    + method_indent
    + "        )\n"
    + "\n"
    + method_indent
    + "    return {\n"
    + method_indent
    + '        "available": True,\n'
    + method_indent
    + '        "execution": False,\n'
    + method_indent
    + "    }\n"
    + "\n"
    + "\n"
    + method_indent
    + "def development_create_task(\n"
    + method_indent
    + "    self,\n"
    + method_indent
    + "    *args,\n"
    + method_indent
    + "    **kwargs,\n"
    + method_indent
    + "):\n"
    + method_indent
    + '    """Tao Development Contract, khong tu dong thuc thi."""\n'
    + method_indent
    + "    support = getattr(\n"
    + method_indent
    + "        self,\n"
    + method_indent
    + '        "development_support",\n'
    + method_indent
    + "        None,\n"
    + method_indent
    + "    )\n"
    + "\n"
    + method_indent
    + "    if support is None:\n"
    + method_indent
    + "        return None\n"
    + "\n"
    + method_indent
    + "    method = getattr(\n"
    + method_indent
    + "        support,\n"
    + method_indent
    + '        "create_contract",\n'
    + method_indent
    + "        None,\n"
    + method_indent
    + "    )\n"
    + "\n"
    + method_indent
    + "    if not callable(method):\n"
    + method_indent
    + "        return None\n"
    + "\n"
    + method_indent
    + "    return method(\n"
    + method_indent
    + "        *args,\n"
    + method_indent
    + "        **kwargs,\n"
    + method_indent
    + "    )\n"
    + "\n"
    + "\n"
    + method_indent
    + "def development_get_status(\n"
    + method_indent
    + "    self,\n"
    + method_indent
    + "    *args,\n"
    + method_indent
    + "    **kwargs,\n"
    + method_indent
    + "):\n"
    + method_indent
    + '    """Lay Development Support status."""\n'
    + method_indent
    + "    return self.development_status()\n"
    + "\n"
    + "\n"
    + method_indent
    + "def development_change_request(\n"
    + method_indent
    + "    self,\n"
    + method_indent
    + "    *args,\n"
    + method_indent
    + "    **kwargs,\n"
    + method_indent
    + "):\n"
    + method_indent
    + '    """Tao Change Request; khong tu dong approve."""\n'
    + method_indent
    + "    support = getattr(\n"
    + method_indent
    + "        self,\n"
    + method_indent
    + '        "development_support",\n'
    + method_indent
    + "        None,\n"
    + method_indent
    + "    )\n"
    + "\n"
    + method_indent
    + "    if support is None:\n"
    + method_indent
    + "        return None\n"
    + "\n"
    + method_indent
    + "    method = getattr(\n"
    + method_indent
    + "        support,\n"
    + method_indent
    + '        "request_change",\n'
    + method_indent
    + "        None,\n"
    + method_indent
    + "    )\n"
    + "\n"
    + method_indent
    + "    if not callable(method):\n"
    + method_indent
    + "        return None\n"
    + "\n"
    + method_indent
    + "    return method(\n"
    + method_indent
    + "        *args,\n"
    + method_indent
    + "        **kwargs,\n"
    + method_indent
    + "    )\n"
    + "\n"
)


source = (
    source[:process_pos]
    + api
    + source[process_pos:]
)


# ============================================================
# 4. WRITE
# ============================================================

MAIN.write_text(
    source,
    encoding="utf-8",
)


# ============================================================
# 5. COMPILE
# ============================================================

try:
    py_compile.compile(
        str(MAIN),
        doraise=True,
    )
except Exception as exc:
    fail(
        "COMPILE FAIL: " + repr(exc)
    )

print("COMPILE: PASS")


# ============================================================
# 6. IMPORT
# ============================================================

try:
    sys.modules.pop("main", None)

    module = importlib.import_module(
        "main"
    )

    MINH = getattr(
        module,
        "MINH",
        None,
    )

    if MINH is None:
        raise RuntimeError(
            "Khong tim thay MINH."
        )

except Exception as exc:
    fail(
        "IMPORT FAIL: " + repr(exc)
    )

print("IMPORT: PASS")


# ============================================================
# 7. DEVELOPMENT SUPPORT VERIFY
# ============================================================

try:
    s = MINH.status()

    if s.get(
        "development_support"
    ) is not True:
        raise RuntimeError(
            "development_support != True"
        )

    if s.get(
        "development_support_mode"
    ) != "development_management":
        raise RuntimeError(
            "development_support_mode sai"
        )

    if s.get(
        "development_support_execution"
    ) is not False:
        raise RuntimeError(
            "development_support_execution != False"
        )

    if not callable(
        getattr(
            MINH,
            "development_status",
            None,
        )
    ):
        raise RuntimeError(
            "development_status khong callable"
        )

    if not callable(
        getattr(
            MINH,
            "development_create_task",
            None,
        )
    ):
        raise RuntimeError(
            "development_create_task khong callable"
        )

    if not callable(
        getattr(
            MINH,
            "development_change_request",
            None,
        )
    ):
        raise RuntimeError(
            "development_change_request khong callable"
        )

    ds_status = MINH.development_status()

    if not isinstance(
        ds_status,
        dict,
    ):
        raise RuntimeError(
            "development_status khong tra dict"
        )

    if ds_status.get(
        "execution"
    ) is not False:
        raise RuntimeError(
            "Development Support execution phai False"
        )

except Exception as exc:
    fail(
        "DEVELOPMENT SUPPORT VERIFY FAIL: "
        + repr(exc)
    )

print(
    "DEVELOPMENT SUPPORT VERIFY: PASS"
)


# ============================================================
# 8. DEBATE REGRESSION
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

    if s.get(
        "debate"
    ) is not True:
        raise RuntimeError(
            "DEBATE != True"
        )

    if s.get(
        "debate_mode"
    ) != "analysis_only":
        raise RuntimeError(
            "DEBATE mode sai"
        )

    if s.get(
        "debate_execution"
    ) is not False:
        raise RuntimeError(
            "DEBATE execution != False"
        )

    if getattr(
        MINH,
        "last_execution_verification",
        None,
    ) is not None:
        raise RuntimeError(
            "DEBATE cham vao P4-5"
        )

except Exception as exc:
    fail(
        "DEBATE REGRESSION FAIL: "
        + repr(exc)
    )

print(
    "DEBATE REGRESSION: PASS"
)


# ============================================================
# FINAL
# ============================================================

print("")
print("=" * 60)
print("DEVELOPMENT SUPPORT INTEGRATION COMPLETE")
print("=" * 60)
print("FILE                 :", MAIN)
print("BACKUP               :", BACKUP)
print("COMPILE              : PASS")
print("IMPORT               : PASS")
print("INIT                 : PASS")
print("STATUS               : PASS")
print("DEVELOPMENT API      : PASS")
print("DEBATE               : PRESERVED")
print("DEBATE REGRESSION    : PASS")
print("P4-5                 : PRESERVED")
print("EXECUTION CONTROLLER : PRESERVED")
print("EXECUTION CONTRACT   : PRESERVED")
print("AUTO EXECUTION       : NOT ADDED")
print("=" * 60)
