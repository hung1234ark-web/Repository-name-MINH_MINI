from pathlib import Path
import shutil
import py_compile
import sys
import importlib


APP = Path(__file__).resolve().parent
MAIN = APP / "main.py"
BACKUP = APP / "main.py.before_development_support"

MARKER = "DEVELOPMENT_SUPPORT_INTEGRATED"


def fail(message):
    print("")
    print("============================================================")
    print("DEVELOPMENT SUPPORT INTEGRATION: FAIL")
    print("============================================================")
    print(message)
    sys.exit(1)


# ============================================================
# LOAD
# ============================================================

if not MAIN.exists():
    fail(f"Khong tim thay {MAIN}")

source = MAIN.read_text(encoding="utf-8")


# ============================================================
# SAFETY CHECK
# ============================================================

if MARKER in source:
    fail(
        "Development Support da duoc tich hop truoc do. "
        "Khong patch lai."
    )

required = [
    "DEBATE_1_1_INIT",
    "DEBATE_1_1_GATE",
    'def process_debate(',
    'def process(',
    '"debate_execution": False',
    "verify_execution_result",
    "ExecutionController",
]

for item in required:
    if item not in source:
        fail(
            "Khong tim thay cau truc bat buoc: "
            + item
        )


# ============================================================
# BACKUP
# ============================================================

shutil.copy2(
    MAIN,
    BACKUP,
)

print("BACKUP CREATED:", BACKUP)


# ============================================================
# 1. INIT
#
# Khong them module-level import.
# Import truc tiep trong class init.
# ============================================================

init_anchor = """# DEBATE_1_1_INIT
"""

if source.count(init_anchor) != 1:
    fail(
        "DEBATE_1_1_INIT khong xuat hien dung 1 lan."
    )

development_init = """# DEVELOPMENT_SUPPORT_INTEGRATED
        # Development Support:
        # - quan ly Development Contract
        # - quan ly task history
        # - loc context
        # - quan ly Change Request
        # - KHONG tu dong thuc thi task
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

source = source.replace(
    init_anchor,
    development_init + init_anchor,
    1,
)


# ============================================================
# 2. STATUS
# ============================================================

status_anchor = """              "debate": (
                  self.debate is not None
              ),
"""

if source.count(status_anchor) != 1:
    fail(
        "Khong tim thay status debate block dung 1 lan."
    )

development_status = """              "development_support": (
                  self.development_support is not None
              ),
              "development_support_mode": (
                  "development_management"
                  if self.development_support is not None
                  else "unavailable"
              ),
              "development_support_execution": False,
"""

source = source.replace(
    status_anchor,
    development_status + status_anchor,
    1,
)


# ============================================================
# 3. PUBLIC API
# ============================================================

api_anchor = """      def process_debate(
"""

if source.count(api_anchor) != 1:
    fail(
        "Khong tim thay process_debate() dung 1 lan."
    )

api = """      # --------------------------------------------------------
      # DEVELOPMENT SUPPORT PUBLIC API
      # --------------------------------------------------------

      def development_status(
          self,
      ) -> dict[str, Any]:
          \"\"\"
          Trang thai Development Support.

          Day la development-management layer.
          Khong thuc thi Action/Web/Ollama.
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
          \"\"\"
          Tao Development Contract.

          Khong thuc thi task.
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
          \"\"\"Lay status cua Development Support.\"\"\"
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

source = source.replace(
    api_anchor,
    api + api_anchor,
    1,
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

    shutil.copy2(
        BACKUP,
        MAIN,
    )

    try:
        py_compile.compile(
            str(MAIN),
            doraise=True,
        )
        print("ROLLBACK: PASS")
    except Exception as rollback_exc:
        print("ROLLBACK: FAIL")
        print(repr(rollback_exc))

    sys.exit(1)

print("COMPILE: PASS")


# ============================================================
# IMPORT
# ============================================================

try:
    if "main" in sys.modules:
        del sys.modules["main"]

    main_module = importlib.import_module("main")
    MINH = getattr(
        main_module,
        "MINH",
        None,
    )

    if MINH is None:
        raise RuntimeError(
            "Khong tim thay MINH."
        )

except Exception as exc:
    print("")
    print("IMPORT: FAIL")
    print(repr(exc))
    print("ROLLBACK...")

    shutil.copy2(
        BACKUP,
        MAIN,
    )

    sys.exit(1)

print("IMPORT: PASS")


# ============================================================
# DEVELOPMENT SUPPORT RUNTIME
# ============================================================

try:
    status = MINH.status()

    if status.get(
        "development_support"
    ) is not True:
        raise RuntimeError(
            "development_support != True"
        )

    if status.get(
        "development_support_mode"
    ) != "development_management":
        raise RuntimeError(
            "development_support_mode sai"
        )

    if status.get(
        "development_support_execution"
    ) is not False:
        raise RuntimeError(
            "development_support_execution phai False"
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
            "development_get_status",
            None,
        )
    ):
        raise RuntimeError(
            "development_get_status khong callable"
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

except Exception as exc:
    print("")
    print("DEVELOPMENT SUPPORT RUNTIME: FAIL")
    print(repr(exc))
    print("ROLLBACK...")

    shutil.copy2(
        BACKUP,
        MAIN,
    )

    try:
        py_compile.compile(
            str(MAIN),
            doraise=True,
        )
        print("ROLLBACK: PASS")
    except Exception as rollback_exc:
        print("ROLLBACK: FAIL")
        print(repr(rollback_exc))

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
            "DEBATE execution phai False"
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

    shutil.copy2(
        BACKUP,
        MAIN,
    )

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
print("CONTEXT API          : CORE PRESERVED")
print("CHANGE REQUEST API   : PASS")
print("DEBATE               : PRESERVED")
print("DEBATE REGRESSION    : PASS")
print("P4-5                 : PRESERVED")
print("EXECUTION CONTROLLER : PRESERVED")
print("EXECUTION CONTRACT   : PRESERVED")
print("AUTO EXECUTION       : NOT ADDED")
print("============================================================")
