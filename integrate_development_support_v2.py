from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
BACKUP = ROOT / "main.py.before_development_support_v2"

source = MAIN.read_text(encoding="utf-8")

# ============================================================
# SAFETY CHECK — BEFORE MODIFY
# ============================================================

required = [
    "DEBATE_1_1_GATE",
    "def process_debate(",
    "def verify_execution_result(",
    "ExecutionController",
    "execution_contract",
]

for marker in required:
    if marker not in source:
        raise RuntimeError(
            f"SAFETY CHECK FAILED. Missing marker: {marker}"
        )

if "DEVELOPMENT_SUPPORT_1_0_INIT" in source:
    raise RuntimeError(
        "DEVELOPMENT SUPPORT ALREADY INTEGRATED."
    )

# ============================================================
# FIND IMPORT ANCHOR
# ============================================================

IMPORT_ANCHOR = 'chat_module = safe_import("chat")'

if IMPORT_ANCHOR not in source:
    raise RuntimeError(
        "SAFETY CHECK FAILED. chat_module import anchor not found."
    )

# ============================================================
# FIND DEBATE INIT ANCHOR
# ============================================================

DEBATE_INIT_ANCHOR = "# DEBATE_1_1_INIT"

if DEBATE_INIT_ANCHOR not in source:
    raise RuntimeError(
        "SAFETY CHECK FAILED. DEBATE init anchor not found."
    )

# ============================================================
# FIND STATUS ANCHOR
# ============================================================

STATUS_ANCHOR = '"debate_execution": False,'

if STATUS_ANCHOR not in source:
    raise RuntimeError(
        "SAFETY CHECK FAILED. DEBATE status anchor not found."
    )

# ============================================================
# FIND PROCESS_DEBATE
# ============================================================

PROCESS_DEBATE_ANCHOR = "    def process_debate("

if source.count(PROCESS_DEBATE_ANCHOR) != 1:
    raise RuntimeError(
        "SAFETY CHECK FAILED. Expected exactly one process_debate()."
    )

# ============================================================
# 1. IMPORT
# ============================================================

IMPORT_BLOCK = '''
    # DEVELOPMENT_SUPPORT_1_0_IMPORT
    development_support_module = safe_import(
        "development_support"
    )
'''

updated = source.replace(
    IMPORT_ANCHOR,
    IMPORT_ANCHOR + "\n" + IMPORT_BLOCK.rstrip(),
    1,
)

# ============================================================
# 2. INIT
# ============================================================

INIT_BLOCK = '''
# DEVELOPMENT_SUPPORT_1_0_INIT
# Development Support la lop quan ly task phat trien.
# Khong phai runtime executor.
try:
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

'''

updated = updated.replace(
    DEBATE_INIT_ANCHOR,
    INIT_BLOCK.rstrip() + "\n" + DEBATE_INIT_ANCHOR,
    1,
)

# ============================================================
# 3. STATUS
# ============================================================

STATUS_BLOCK = '''
    "development_support": (
        self.development_support is not None
    ),
    "development_support_mode": (
        "contract_management"
        if self.development_support is not None
        else "unavailable"
    ),
    "development_support_execution": False,
'''

updated = updated.replace(
    STATUS_ANCHOR,
    STATUS_ANCHOR + "\n" + STATUS_BLOCK.rstrip(),
    1,
)

# ============================================================
# 4. PUBLIC API
# ============================================================

API_BLOCK = '''
    # --------------------------------------------------------
    # DEVELOPMENT SUPPORT API
    # --------------------------------------------------------

    def development_create_task(
        self,
        title: str,
        goal: str,
        scope=None,
        allowed_files=None,
        forbidden_files=None,
        permissions=None,
        requirements=None,
        success_criteria=None,
    ):
        """
        Create a Development Contract.

        This API only creates a development task.
        It does NOT execute code or tools.
        """

        if self.development_support is None:
            return None

        return self.development_support.create_contract(
            title=title,
            goal=goal,
            scope=scope,
            allowed_files=allowed_files,
            forbidden_files=forbidden_files,
            permissions=permissions,
            requirements=requirements,
            success_criteria=success_criteria,
        )

    def development_get_status(
        self,
        task_id=None,
    ):
        if self.development_support is None:
            return {
                "module": "development_support",
                "status": "UNAVAILABLE",
            }

        if task_id is None:
            active_task_id = (
                self.development_support.active_task_id
            )

            if active_task_id is None:
                return {
                    "module": "development_support",
                    "version": "DEVELOPMENT-SUPPORT-1.0",
                    "active_task_id": None,
                    "status": "IDLE",
                }

            return self.development_support.status(
                active_task_id
            )

        return self.development_support.status(task_id)

    def development_approve(
        self,
        task_id=None,
    ):
        if self.development_support is None:
            return None

        return self.development_support.approve_contract(
            task_id
        )

    def development_lock(
        self,
        task_id=None,
    ):
        if self.development_support is None:
            return None

        return self.development_support.lock_contract(
            task_id
        )

    def development_context(
        self,
        task_id=None,
        files=None,
        extra_context=None,
    ):
        if self.development_support is None:
            return None

        return self.development_support.build_context(
            task_id=task_id,
            files=files,
            extra_context=extra_context,
        )

    def development_change_request(
        self,
        reason: str,
        requested_changes,
        task_id=None,
    ):
        if self.development_support is None:
            return None

        return self.development_support.create_change_request(
            reason=reason,
            requested_changes=requested_changes,
            task_id=task_id,
        )

    def development_resolve_change(
        self,
        request_id: str,
        approved: bool,
        note: str = "",
    ):
        if self.development_support is None:
            return None

        return self.development_support.resolve_change_request(
            request_id=request_id,
            approved=approved,
            note=note,
        )

'''

updated = updated.replace(
    PROCESS_DEBATE_ANCHOR,
    API_BLOCK.rstrip() + "\n\n" + PROCESS_DEBATE_ANCHOR,
    1,
)

# ============================================================
# SAFETY CHECK — AFTER MODIFY
# ============================================================

checks = {
    "development_import": (
        "DEVELOPMENT_SUPPORT_1_0_IMPORT" in updated
    ),
    "development_init": (
        "DEVELOPMENT_SUPPORT_1_0_INIT" in updated
    ),
    "development_status": (
        '"development_support": (' in updated
    ),
    "development_mode": (
        '"development_support_mode": (' in updated
    ),
    "development_execution_disabled": (
        '"development_support_execution": False,' in updated
    ),
    "development_create": (
        "def development_create_task(" in updated
    ),
    "development_status_api": (
        "def development_get_status(" in updated
    ),
    "development_approve": (
        "def development_approve(" in updated
    ),
    "development_lock": (
        "def development_lock(" in updated
    ),
    "development_context": (
        "def development_context(" in updated
    ),
    "development_change_request": (
        "def development_change_request(" in updated
    ),
    "development_resolve_change": (
        "def development_resolve_change(" in updated
    ),
    "debate_preserved": (
        "DEBATE_1_1_GATE" in updated
        and "def process_debate(" in updated
    ),
    "p45_preserved": (
        "def verify_execution_result(" in updated
    ),
    "execution_controller_preserved": (
        "ExecutionController" in updated
    ),
    "execution_contract_preserved": (
        "execution_contract" in updated
    ),
    "no_development_handler": (
        '"development_support": handle_' not in updated
    ),
}

failed = [
    name
    for name, result in checks.items()
    if not result
]

if failed:
    raise RuntimeError(
        "SAFETY CHECK FAILED:\n- "
        + "\n- ".join(failed)
    )

if updated.count("DEVELOPMENT_SUPPORT_1_0_INIT") != 1:
    raise RuntimeError(
        "SAFETY CHECK FAILED. Duplicate Development Support init."
    )

if updated.count("def development_create_task(") != 1:
    raise RuntimeError(
        "SAFETY CHECK FAILED. Duplicate Development Support API."
    )

# ============================================================
# BACKUP
# ============================================================

if not BACKUP.exists():
    shutil.copy2(MAIN, BACKUP)

# ============================================================
# WRITE ONLY AFTER ALL CHECKS PASS
# ============================================================

MAIN.write_text(
    updated,
    encoding="utf-8",
)

print()
print("=" * 60)
print("DEVELOPMENT SUPPORT INTEGRATION V2 COMPLETE")
print("=" * 60)
print(f"FILE                 : {MAIN}")
print(f"BACKUP               : {BACKUP}")
print("IMPORT               : PASS")
print("INIT                 : PASS")
print("STATUS               : PASS")
print("TASK API             : PASS")
print("CONTRACT API         : PASS")
print("CONTEXT API          : PASS")
print("CHANGE REQUEST API   : PASS")
print("DEBATE               : PRESERVED")
print("P4-5                 : PRESERVED")
print("EXECUTION CONTROLLER : PRESERVED")
print("EXECUTION CONTRACT   : PRESERVED")
print("AUTO EXECUTION       : NOT ADDED")
print("=" * 60)
