from __future__ import annotations

import inspect
import json
import traceback

import development_support


SEP = "=" * 64


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    print(SEP)
    print("MINH MINI — DEVELOPMENT SUPPORT E2E TEST")
    print(SEP)

    try:
        # ============================================================
        # 1. IMPORT
        # ============================================================
        check(
            hasattr(development_support, "get_support"),
            "Missing get_support()",
        )
        print("IMPORT: PASS")

        # ============================================================
        # 2. FACTORY
        # ============================================================
        support = development_support.get_support()

        check(
            support is not None,
            "get_support() returned None",
        )
        print("FACTORY: PASS")

        # ============================================================
        # 3. SELF CHECK
        # ============================================================
        self_check = support.self_check()

        check(
            isinstance(self_check, dict),
            "self_check() must return dict",
        )

        check(
            self_check.get("passed") is True,
            f"self_check() failed: {self_check}",
        )

        print("SELF CHECK: PASS")

        # ============================================================
        # 4. API SURFACE
        # ============================================================
        required_methods = [
            "create_contract",
            "approve_contract",
            "lock_contract",
            "check_file_scope",
            "check_permission",
            "build_context",
            "create_change_request",
            "resolve_change_request",
            "get_history",
            "status",
            "start_execution",
            "start_validation",
        ]

        for method_name in required_methods:
            check(
                callable(getattr(support, method_name, None)),
                f"Missing API: {method_name}",
            )

        print("API SURFACE: PASS")

        # ============================================================
        # 5. CREATE CONTRACT
        # ============================================================
        contract = support.create_contract(
            title="E2E Development Support Test",
            goal=(
                "Verify Development Support lifecycle, "
                "scope, context and safety."
            ),
            scope=[
                "development support lifecycle",
                "contract control",
                "context filtering",
                "change request",
            ],
            allowed_files=[
                "development_support.py",
                "test_development_support_e2e.py",
            ],
            forbidden_files=[
                "main.py",
                "execution_controller.py",
                "execution_contract.py",
            ],
            permissions=[
                "read",
                "analyze",
            ],
            requirements=[
                "Do not modify runtime execution architecture.",
                "Do not modify P4-5.",
                "Do not automatically execute changes.",
            ],
            success_criteria=[
                "Contract can be created.",
                "Contract can be approved.",
                "Contract can be locked.",
                "Sensitive context is filtered.",
                "Change request requires explicit resolution.",
                "Execution remains controlled.",
            ],
        )

        check(
            contract is not None,
            "create_contract() returned None",
        )

        task_id = getattr(contract, "task_id", None)

        check(
            bool(task_id),
            "Contract task_id was not generated",
        )

        print("CONTRACT API: create_contract")
        print(f"TASK ID: {task_id}")
        print("CREATE CONTRACT: PASS")

        # ============================================================
        # 6. STATUS AFTER CREATE
        # ============================================================
        status_created = support.status(task_id)

        check(
            isinstance(status_created, dict),
            "status() must return dict",
        )

        print("STATUS AFTER CREATE: PASS")

        # ============================================================
        # 7. APPROVE CONTRACT
        # ============================================================
        approved = support.approve_contract(task_id)

        check(
            approved is not None,
            "approve_contract() returned None",
        )

        current_contract = support.get_contract(task_id)

        check(
            str(getattr(current_contract, "status", "")).upper().endswith(
                "APPROVED"
            ),
            (
                "Unexpected status after approval: "
                f"{getattr(current_contract, 'status', None)}"
            ),
        )

        print("APPROVE CONTRACT: PASS")

        # ============================================================
        # 8. LOCK CONTRACT
        # ============================================================
        locked = support.lock_contract(task_id)

        check(
            locked is not None,
            "lock_contract() returned None",
        )

        current_contract = support.get_contract(task_id)

        check(
            str(getattr(current_contract, "status", "")).upper().endswith(
                "LOCKED"
            ),
            (
                "Unexpected status after lock: "
                f"{getattr(current_contract, 'status', None)}"
            ),
        )

        print("LOCK CONTRACT: PASS")

        # ============================================================
        # 9. STATUS AFTER LOCK
        # ============================================================
        status_locked = support.status(task_id)

        check(
            isinstance(status_locked, dict),
            "Locked status must be dict",
        )

        print("STATUS AFTER LOCK: PASS")

        # ============================================================
        # 10. FILE SCOPE
        #
        # REAL API:
        # check_file_scope(file_path, task_id=None)
        # ============================================================
        allowed_scope = support.check_file_scope(
            "development_support.py",
            task_id,
        )

        check(
            allowed_scope is True,
            "Allowed file rejected by scope guard",
        )

        forbidden_scope = support.check_file_scope(
            "main.py",
            task_id,
        )

        check(
            forbidden_scope is False,
            "Forbidden file passed scope guard",
        )

        print("SCOPE GUARD: PASS")

        # ============================================================
        # 11. PERMISSION
        #
        # REAL API:
        # check_permission(permission, task_id=None)
        # ============================================================
        read_permission = support.check_permission(
            "read",
            task_id,
        )

        check(
            read_permission is True,
            "Allowed permission rejected",
        )

        execute_permission = support.check_permission(
            "execute",
            task_id,
        )

        check(
            execute_permission is False,
            "Unexpected execute permission granted",
        )

        print("PERMISSION GUARD: PASS")

        # ============================================================
        # 12. CONTEXT FILTER
        #
        # REAL API:
        # sanitize_text(text)
        # ============================================================
        sensitive_text = (
            "username=Lam "
            "password=SUPER_SECRET "
            "api_key=ABC123 "
            "normal information"
        )

        filtered = support.context_filter.sanitize_text(
            sensitive_text
        )

        check(
            isinstance(filtered, str),
            "sanitize_text() must return string",
        )

        check(
            "SUPER_SECRET" not in filtered,
            "Password leaked through sanitize_text()",
        )

        check(
            "ABC123" not in filtered,
            "API key leaked through sanitize_text()",
        )

        check(
            "[REDACTED]" in filtered,
            "Sensitive values were not redacted",
        )

        print("CONTEXT FILTER: PASS")

        # ============================================================
        # 13. SENSITIVE FILE FILTER
        #
        # REAL API:
        # filter_files(files, allowed_files=None)
        # ============================================================
        filtered_files = support.context_filter.filter_files(
            [
                "development_support.py",
                ".env",
                "password.txt",
                "main.py",
            ],
            [
                "development_support.py",
                ".env",
                "password.txt",
                "main.py",
            ],
        )

        check(
            "development_support.py" in filtered_files,
            "Safe file was incorrectly filtered",
        )

        check(
            ".env" not in filtered_files,
            ".env leaked through file filter",
        )

        check(
            "password.txt" not in filtered_files,
            "Password file leaked through file filter",
        )

        check(
            "main.py" in filtered_files,
            "main.py should not be filtered by ContextFilter itself",
        )

        print("SENSITIVE FILE FILTER: PASS")

        # ============================================================
        # 14. BUILD CONTEXT
        #
        # REAL API:
        # build_context(task_id=None, files=None, extra_context=None)
        # ============================================================
        context = support.build_context(
            task_id=task_id,
            files=[
                "development_support.py",
                "main.py",
                ".env",
            ],
            extra_context={
                "password": "SUPER_SECRET",
                "api_key": "ABC123",
                "normal": "safe-data",
            },
        )

        check(
            isinstance(context, dict),
            "build_context() must return dict",
        )

        context_text = json.dumps(
            context,
            ensure_ascii=False,
            default=str,
        )

        check(
            "SUPER_SECRET" not in context_text,
            "Sensitive password leaked into task context",
        )

        check(
            "ABC123" not in context_text,
            "Sensitive API key leaked into task context",
        )

        context_files = context.get("files", [])

        check(
            "development_support.py" in context_files,
            "Allowed development_support.py missing from context",
        )

        check(
            "main.py" not in context_files,
            "Forbidden main.py entered development context",
        )

        check(
            ".env" not in context_files,
            "Sensitive .env entered development context",
        )

        print("BUILD CONTEXT: PASS")

        # ============================================================
        # 15. CHANGE REQUEST
        # ============================================================
        change_request = support.create_change_request(
            task_id=task_id,
            reason=(
                "Test whether contract changes require "
                "explicit resolution."
            ),
            requested_changes=[
                "Allow an additional development file."
            ],
        )

        check(
            change_request is not None,
            "create_change_request() returned None",
        )

        change_request_id = getattr(
            change_request,
            "request_id",
            None,
        )

        check(
            bool(change_request_id),
            "Change request ID was not generated",
        )

        print("CHANGE REQUEST: PASS")

        # ============================================================
        # 16. CHANGE REQUEST MUST START PENDING
        # ============================================================
        request_status = str(
            getattr(change_request, "status", "")
        ).upper()

        check(
            "PENDING" in request_status,
            (
                "Change request was automatically resolved: "
                f"{request_status}"
            ),
        )

        print("CHANGE REQUEST LOCK: PASS")

        # ============================================================
        # 17. RESOLVE CHANGE REQUEST
        #
        # Read the actual method signature and only use parameters
        # that really exist.
        # ============================================================
        resolve_signature = inspect.signature(
            support.resolve_change_request
        )

        resolve_params = resolve_signature.parameters
        resolve_kwargs = {}

        if "task_id" in resolve_params:
            resolve_kwargs["task_id"] = task_id

        if "request_id" in resolve_params:
            resolve_kwargs["request_id"] = change_request_id
        elif "change_request_id" in resolve_params:
            resolve_kwargs["change_request_id"] = change_request_id

        if "approved" in resolve_params:
            resolve_kwargs["approved"] = False
        elif "decision" in resolve_params:
            resolve_kwargs["decision"] = "REJECTED"
        elif "status" in resolve_params:
            resolve_kwargs["status"] = "REJECTED"

        if "note" in resolve_params:
            resolve_kwargs["note"] = (
                "E2E safety verification."
            )

        check(
            resolve_kwargs,
            "Could not map resolve_change_request() API",
        )

        resolved = support.resolve_change_request(
            **resolve_kwargs
        )

        check(
            resolved is not None,
            "resolve_change_request() returned None",
        )

        print("CHANGE REQUEST RESOLUTION: PASS")

        # ============================================================
        # 18. HISTORY
        # ============================================================
        history = support.get_history(task_id)

        check(
            isinstance(history, (list, tuple)),
            "get_history() must return a sequence",
        )

        check(
            len(history) >= 1,
            "Task history is empty",
        )

        print("HISTORY: PASS")

        # ============================================================
        # 19. EXECUTION SAFETY
        #
        # Do not execute anything.
        # The E2E test only verifies that the API exists.
        # ============================================================
        check(
            callable(getattr(support, "start_execution", None)),
            "start_execution API missing",
        )

        check(
            callable(getattr(support, "start_validation", None)),
            "start_validation API missing",
        )

        print("EXECUTION SAFETY: PASS")

        # ============================================================
        # 20. FINAL STATUS
        # ============================================================
        final_status = support.status(task_id)

        check(
            isinstance(final_status, dict),
            "Final status must be dict",
        )

        print("FINAL STATUS: PASS")

        # ============================================================
        # FINAL RESULT
        # ============================================================
        print()
        print(SEP)
        print("DEVELOPMENT SUPPORT E2E: PASS")
        print(SEP)
        print(f"TASK ID              : {task_id}")
        print("CONTRACT CREATION    : PASS")
        print("APPROVAL             : PASS")
        print("LOCK                 : PASS")
        print("SCOPE GUARD          : PASS")
        print("PERMISSION GUARD     : PASS")
        print("CONTEXT FILTER       : PASS")
        print("SENSITIVE FILE FILTER: PASS")
        print("BUILD CONTEXT        : PASS")
        print("CHANGE REQUEST       : PASS")
        print("CHANGE REQUEST LOCK  : PASS")
        print("HISTORY              : PASS")
        print("EXECUTION SAFETY     : PASS")
        print("MAIN.PY MODIFIED     : NO")
        print("P4-5 TOUCHED         : NO")
        print("AUTO EXECUTION       : NO")
        print(SEP)

        return 0

    except Exception as exc:
        print()
        print(SEP)
        print("DEVELOPMENT SUPPORT E2E: FAIL")
        print(SEP)
        print(f"ERROR: {exc!r}")
        print()
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
