from pathlib import Path
import shutil
import py_compile
import sys


APP = Path(__file__).resolve().parent
MAIN = APP / "main.py"
BACKUP = APP / "main.py.before_development_support_v3"


def fail(message):
    print("")
    print("DEVELOPMENT SUPPORT INTEGRATION V3: FAIL")
    print(message)
    sys.exit(1)


if not MAIN.exists():
    fail(f"Khong tim thay: {MAIN}")


source = MAIN.read_text(encoding="utf-8")


# ============================================================
# SAFETY
# ============================================================

if "DEVELOPMENT_SUPPORT_1_0_INIT" in source:
    fail("main.py da co DEVELOPMENT_SUPPORT_1_0_INIT. Khong patch lan 2.")

if "development_support" in source:
    fail(
        "main.py da co dau vet development_support. "
        "Khong tu dong patch tiep de tranh trung lap."
    )

if "DEBATE_1_1_INIT" not in source:
    fail("Khong tim thay DEBATE_1_1_INIT.")

if "def process_debate(" not in source:
    fail("Khong tim thay def process_debate().")

if '"debate_execution": False' not in source:
    fail('Khong tim thay status marker "debate_execution": False.')

if "def process(" not in source:
    fail("Khong tim thay def process().")


# ============================================================
# BACKUP
# ============================================================

shutil.copy2(MAIN, BACKUP)


# ============================================================
# 1. DEVELOPMENT SUPPORT INIT
#
# Import nam ben trong class method.
# Khong them module-level import de tranh loi indentation
# da xay ra o V2.
# ============================================================

init_marker = """# DEBATE_1_1_INIT
"""

if source.count(init_marker) != 1:
    fail(
        "DEBATE_1_1_INIT khong xuat hien dung 1 lan."
    )


development_init = """# DEVELOPMENT_SUPPORT_1_0_INIT
        # Development Support la lop quan ly qua trinh phat trien.
        # Khong phai execution handler.
        # Khong duoc tu dong thuc thi task.
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
    init_marker,
    development_init + init_marker,
    1,
)


# ============================================================
# 2. STATUS
# ============================================================

status_marker = """              "debate": (
                  self.debate is not None
              ),
"""

if source.count(status_marker) != 1:
    fail(
        "Khong tim thay status debate block dung 1 lan."
    )


status_insert = """              "development_support": (
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
    status_marker,
    status_insert + status_marker,
    1,
)


# ============================================================
# 3. DEVELOPMENT SUPPORT PUBLIC API
#
# API chi lam viec voi Development Support.
# Khong goi ExecutionController.
# Khong goi Action/Web/Ollama.
# ============================================================

process_debate_marker = """      def process_debate(
"""

if source.count(process_debate_marker) != 1:
    fail(
        "Khong tim thay vi tri process_debate() dung 1 lan."
    )


development_api = """      # --------------------------------------------------------
      # DEVELOPMENT SUPPORT
      # --------------------------------------------------------

      def development_status(
          self,
      ) -> dict[str, Any]:
          \"\"\"
          Tra ve trang thai Development Support.

          Chi quan ly development task/contract/context/change request.
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
              status_method = getattr(
                  support,
                  "status",
                  None,
              )

              if callable(status_method):
                  result = status_method()

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
          Public bridge cho Development Support task creation.

          Chi goi API cua Development Support.
          Khong thuc thi task.
          \"\"\"
          support = getattr(
              self,
              "development_support",
              None,
          )

          if support is None:
              return None

          creator = getattr(
              support,
              "create_contract",
              None,
          )

          if not callable(creator):
              return None

          return creator(
              *args,
              **kwargs,
          )


      def development_get_status(
          self,
          *args,
          **kwargs,
      ):
          \"\"\"Public status bridge cho Development Support.\"\"\"
          return self.development_status()


      def development_change_request(
          self,
          *args,
          **kwargs,
      ):
          \"\"\"
          Public bridge cho Change Request.

          Change Request khong tu dong duoc approve.
          \"\"\"
          support = getattr(
              self,
              "development_support",
              None,
          )

          if support is None:
              return None

          requester = getattr(
              support,
              "request_change",
              None,
          )

          if not callable(requester):
              return None

          return requester(
              *args,
              **kwargs,
          )


"""

source = source.replace(
    process_debate_marker,
    development_api + process_debate_marker,
    1,
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
    print("")
    print("COMPILE: FAIL")
    print(repr(exc))
    print("")
    print("Dang rollback tu backup V3...")

    shutil.copy2(
        BACKUP,
        MAIN,
    )

    try:
        py_compile.compile(
            str(MAIN),
            doraise=True,
        )
        print("ROLLBACK AFTER FAILURE: PASS")
    except Exception as rollback_exc:
        print("ROLLBACK AFTER FAILURE: FAIL")
        print(repr(rollback_exc))

    sys.exit(1)


# ============================================================
# 6. STRUCTURAL CHECKS
# ============================================================

checks = {
    "DS INIT": "DEVELOPMENT_SUPPORT_1_0_INIT" in source,
    "DS STATUS": '"development_support": (' in source,
    "DS MODE": '"development_support_mode": (' in source,
    "DS EXECUTION FALSE": '"development_support_execution": False' in source,
    "DS TASK API": "def development_create_task(" in source,
    "DS STATUS API": "def development_get_status(" in source,
    "DS CHANGE API": "def development_change_request(" in source,

    # DEBATE protection
    "DEBATE": "DEBATE_1_1_INIT" in source,
    "DEBATE GATE": "DEBATE_1_1_GATE" in source,
    "DEBATE EXECUTION FALSE": '"debate_execution": False' in source,

    # P4-5 protection
    "P45 VERIFY": "verify_execution_result" in source,
    "EXECUTION CONTROLLER": "ExecutionController" in source,
    "EXECUTION CONTRACT": "execution_contract" in source,
}


failed = [
    name
    for name, value in checks.items()
    if not value
]


if failed:
    print("")
    print("STRUCTURAL CHECK: FAIL")
    for item in failed:
        print(" -", item)

    shutil.copy2(
        BACKUP,
        MAIN,
    )

    print("ROLLBACK: PASS")
    sys.exit(1)


# ============================================================
# 7. IMPORT CHECK
# ============================================================

try:
    import importlib

    if "main" in sys.modules:
        del sys.modules["main"]

    main_module = importlib.import_module("main")
    MINH = getattr(main_module, "MINH", None)

    if MINH is None:
        raise RuntimeError("Khong tim thay MINH.")

except Exception as exc:
    print("")
    print("IMPORT CHECK: FAIL")
    print(repr(exc))

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


# ============================================================
# 8. RUNTIME CHECK
# ============================================================

try:
    status = MINH.status()

    if not isinstance(status, dict):
        raise RuntimeError(
            "MINH.status() khong tra ve dict."
        )

    ds = status.get(
        "development_support"
    )

    ds_mode = status.get(
        "development_support_mode"
    )

    ds_execution = status.get(
        "development_support_execution"
    )

    if ds is not True:
        raise RuntimeError(
            "development_support khong True."
        )

    if ds_mode != "development_management":
        raise RuntimeError(
            "development_support_mode khong dung."
        )

    if ds_execution is not False:
        raise RuntimeError(
            "development_support_execution phai False."
        )

    if not callable(
        getattr(
            MINH,
            "development_create_task",
            None,
        )
    ):
        raise RuntimeError(
            "development_create_task khong callable."
        )

    if not callable(
        getattr(
            MINH,
            "development_get_status",
            None,
        )
    ):
        raise RuntimeError(
            "development_get_status khong callable."
        )

    if not callable(
        getattr(
            MINH,
            "development_change_request",
            None,
        )
    ):
        raise RuntimeError(
            "development_change_request khong callable."
        )

except Exception as exc:
    print("")
    print("RUNTIME CHECK: FAIL")
    print(repr(exc))

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


# ============================================================
# 9. DEBATE REGRESSION
# ============================================================

try:
    debate_answer = MINH.process(
        "/debate Có nên thêm một AI mới vào MINH MINI không?"
    )

    debate_status = MINH.status()

    if not debate_answer:
        raise RuntimeError(
            "DEBATE khong tra ve answer."
        )

    if debate_status.get("debate") is not True:
        raise RuntimeError(
            "DEBATE khong True."
        )

    if debate_status.get("debate_mode") != "analysis_only":
        raise RuntimeError(
            "DEBATE mode khong analysis_only."
        )

    if debate_status.get("debate_execution") is not False:
        raise RuntimeError(
            "DEBATE execution khong False."
        )

    if getattr(
        MINH,
        "last_execution_verification",
        None,
    ) is not None:
        raise RuntimeError(
            "DEBATE da cham vao P4-5."
        )

except Exception as exc:
    print("")
    print("DEBATE REGRESSION: FAIL")
    print(repr(exc))

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


# ============================================================
# FINAL
# ============================================================

print("")
print("============================================================")
print("DEVELOPMENT SUPPORT INTEGRATION V3 COMPLETE")
print("============================================================")
print(f"FILE                 : {MAIN}")
print(f"BACKUP               : {BACKUP}")
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
