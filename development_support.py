from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


VERSION = "DEVELOPMENT-SUPPORT-1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class ContractStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"
    EXECUTING = "EXECUTING"
    VALIDATION = "VALIDATION"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ChangeRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class DevelopmentContract:
    task_id: str
    title: str
    goal: str
    scope: List[str] = field(default_factory=list)
    allowed_files: List[str] = field(default_factory=list)
    forbidden_files: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    status: ContractStatus = ContractStatus.DRAFT
    version: int = 1

    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    approved_at: Optional[str] = None
    locked_at: Optional[str] = None

    def touch(self) -> None:
        self.updated_at = _now()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class ChangeRequest:
    request_id: str
    task_id: str
    reason: str
    requested_changes: List[str] = field(default_factory=list)

    status: ChangeRequestStatus = ChangeRequestStatus.PENDING

    created_at: str = field(default_factory=_now)
    resolved_at: Optional[str] = None
    resolution_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class TaskHistoryEntry:
    entry_id: str
    task_id: str
    event: str
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContextFilter:
    """
    Bộ lọc context dành cho Development Support.

    Mục tiêu:
    - Không gửi credential/token/password/API key.
    - Không đưa file nhạy cảm vào context nếu không được phép.
    - Giảm context xuống đúng phạm vi task.
    """

    SENSITIVE_NAMES = (
        ".env",
        ".env.local",
        ".env.production",
        "credentials",
        "credential",
        "secret",
        "secrets",
        "password",
        "passwd",
        "token",
        "api_key",
        "api-key",
        "access_token",
        "access-token",
        "refresh_token",
        "refresh-token",
        "authorization",
        "private_key",
        "private-key",
        "id_rsa",
    )

    SENSITIVE_PATTERNS = (
        re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"),
        re.compile(r"(?i)(access[_-]?token\s*[:=]\s*)[^\s,;]+"),
        re.compile(r"(?i)(refresh[_-]?token\s*[:=]\s*)[^\s,;]+"),
        re.compile(r"(?i)(password\s*[:=]\s*)[^\s,;]+"),
        re.compile(r"(?i)(secret\s*[:=]\s*)[^\s,;]+"),
        re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"),
    )

    def is_sensitive_name(self, value: str) -> bool:
        lowered = str(value).replace("\\", "/").lower()
        basename = lowered.rsplit("/", 1)[-1]

        return any(
            marker in basename or marker in lowered
            for marker in self.SENSITIVE_NAMES
        )

    def sanitize_text(self, text: str) -> str:
        result = str(text)

        for pattern in self.SENSITIVE_PATTERNS:
            result = pattern.sub(r"\1[REDACTED]", result)

        return result

    def filter_files(
        self,
        files: Iterable[str],
        allowed_files: Optional[Sequence[str]] = None,
    ) -> List[str]:
        allowed = {
            str(item).replace("\\", "/").lower()
            for item in (allowed_files or [])
        }

        output: List[str] = []

        for item in files:
            value = str(item)
            normalized = value.replace("\\", "/")
            lowered = normalized.lower()

            if self.is_sensitive_name(normalized):
                continue

            if allowed:
                if lowered not in allowed:
                    continue

            output.append(value)

        return output

    def sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        def sanitize(value: Any) -> Any:
            if isinstance(value, str):
                return self.sanitize_text(value)

            if isinstance(value, dict):
                return {
                    str(key): sanitize(item)
                    for key, item in value.items()
                    if not self.is_sensitive_name(str(key))
                }

            if isinstance(value, list):
                return [sanitize(item) for item in value]

            if isinstance(value, tuple):
                return [sanitize(item) for item in value]

            return value

        return sanitize(context)


class DevelopmentSupport:
    """
    MINH MINI Development Support Core.

    Đây là lớp quản lý quá trình phát triển dự án.
    Nó KHÔNG phải runtime executor và không thay thế:
        - execution_contract.py
        - execution_controller.py
        - P4-5 verification

    Development Support quản lý:
        Development Contract
        Contract Lock
        Context Filter
        Task History
        Change Request
    """

    def __init__(self) -> None:
        self.contracts: Dict[str, DevelopmentContract] = {}
        self.change_requests: Dict[str, ChangeRequest] = {}
        self.history: List[TaskHistoryEntry] = []

        self.context_filter = ContextFilter()
        self.active_task_id: Optional[str] = None

    # ------------------------------------------------------------------
    # HISTORY
    # ------------------------------------------------------------------

    def _record(
        self,
        task_id: str,
        event: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> TaskHistoryEntry:
        entry = TaskHistoryEntry(
            entry_id=_new_id("hist"),
            task_id=task_id,
            event=event,
            details=details or {},
        )

        self.history.append(entry)
        return entry

    def get_history(
        self,
        task_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if task_id is None:
            entries = self.history
        else:
            entries = [
                item
                for item in self.history
                if item.task_id == task_id
            ]

        return [item.to_dict() for item in entries]

    # ------------------------------------------------------------------
    # CONTRACT
    # ------------------------------------------------------------------

    def create_contract(
        self,
        title: str,
        goal: str,
        scope: Optional[Sequence[str]] = None,
        allowed_files: Optional[Sequence[str]] = None,
        forbidden_files: Optional[Sequence[str]] = None,
        permissions: Optional[Sequence[str]] = None,
        requirements: Optional[Sequence[str]] = None,
        success_criteria: Optional[Sequence[str]] = None,
    ) -> DevelopmentContract:
        if not str(title).strip():
            raise ValueError("title is required")

        if not str(goal).strip():
            raise ValueError("goal is required")

        task_id = _new_id("task")

        contract = DevelopmentContract(
            task_id=task_id,
            title=str(title).strip(),
            goal=str(goal).strip(),
            scope=[str(x) for x in (scope or [])],
            allowed_files=[
                str(x)
                for x in (allowed_files or [])
                if not self.context_filter.is_sensitive_name(str(x))
            ],
            forbidden_files=[str(x) for x in (forbidden_files or [])],
            permissions=[str(x) for x in (permissions or [])],
            requirements=[str(x) for x in (requirements or [])],
            success_criteria=[str(x) for x in (success_criteria or [])],
        )

        self.contracts[task_id] = contract
        self.active_task_id = task_id

        self._record(
            task_id,
            "CONTRACT_CREATED",
            {
                "title": contract.title,
                "goal": contract.goal,
            },
        )

        return contract

    def get_contract(
        self,
        task_id: Optional[str] = None,
    ) -> DevelopmentContract:
        task_id = task_id or self.active_task_id

        if not task_id:
            raise ValueError("No active development task")

        if task_id not in self.contracts:
            raise KeyError(f"Unknown task_id: {task_id}")

        return self.contracts[task_id]

    def approve_contract(
        self,
        task_id: Optional[str] = None,
    ) -> DevelopmentContract:
        contract = self.get_contract(task_id)

        if contract.status != ContractStatus.DRAFT:
            raise RuntimeError(
                f"Cannot approve contract from status {contract.status.value}"
            )

        contract.status = ContractStatus.APPROVED
        contract.approved_at = _now()
        contract.touch()

        self._record(
            contract.task_id,
            "CONTRACT_APPROVED",
        )

        return contract

    def lock_contract(
        self,
        task_id: Optional[str] = None,
    ) -> DevelopmentContract:
        contract = self.get_contract(task_id)

        if contract.status != ContractStatus.APPROVED:
            raise RuntimeError(
                f"Cannot lock contract from status {contract.status.value}"
            )

        contract.status = ContractStatus.LOCKED
        contract.locked_at = _now()
        contract.touch()

        self._record(
            contract.task_id,
            "CONTRACT_LOCKED",
        )

        return contract

    def start_execution(
        self,
        task_id: Optional[str] = None,
    ) -> DevelopmentContract:
        contract = self.get_contract(task_id)

        if contract.status != ContractStatus.LOCKED:
            raise RuntimeError(
                f"Cannot start execution from status {contract.status.value}"
            )

        contract.status = ContractStatus.EXECUTING
        contract.touch()

        self._record(
            contract.task_id,
            "EXECUTION_STARTED",
        )

        return contract

    def start_validation(
        self,
        task_id: Optional[str] = None,
    ) -> DevelopmentContract:
        contract = self.get_contract(task_id)

        if contract.status != ContractStatus.EXECUTING:
            raise RuntimeError(
                f"Cannot start validation from status {contract.status.value}"
            )

        contract.status = ContractStatus.VALIDATION
        contract.touch()

        self._record(
            contract.task_id,
            "VALIDATION_STARTED",
        )

        return contract

    def complete_task(
        self,
        task_id: Optional[str] = None,
    ) -> DevelopmentContract:
        contract = self.get_contract(task_id)

        if contract.status != ContractStatus.VALIDATION:
            raise RuntimeError(
                f"Cannot complete task from status {contract.status.value}"
            )

        contract.status = ContractStatus.COMPLETED
        contract.touch()

        self._record(
            contract.task_id,
            "TASK_COMPLETED",
        )

        return contract

    def reject_contract(
        self,
        task_id: Optional[str] = None,
        reason: str = "",
    ) -> DevelopmentContract:
        contract = self.get_contract(task_id)

        if contract.status not in (
            ContractStatus.DRAFT,
            ContractStatus.APPROVED,
        ):
            raise RuntimeError(
                f"Cannot reject contract from status {contract.status.value}"
            )

        contract.status = ContractStatus.REJECTED
        contract.touch()

        self._record(
            contract.task_id,
            "CONTRACT_REJECTED",
            {"reason": str(reason)},
        )

        return contract

    def cancel_task(
        self,
        task_id: Optional[str] = None,
        reason: str = "",
    ) -> DevelopmentContract:
        contract = self.get_contract(task_id)

        if contract.status == ContractStatus.COMPLETED:
            raise RuntimeError("Completed task cannot be cancelled")

        contract.status = ContractStatus.CANCELLED
        contract.touch()

        self._record(
            contract.task_id,
            "TASK_CANCELLED",
            {"reason": str(reason)},
        )

        return contract

    # ------------------------------------------------------------------
    # SCOPE / PERMISSION GUARD
    # ------------------------------------------------------------------

    def check_file_scope(
        self,
        file_path: str,
        task_id: Optional[str] = None,
    ) -> bool:
        contract = self.get_contract(task_id)

        normalized = str(file_path).replace("\\", "/").lower()

        for forbidden in contract.forbidden_files:
            forbidden_normalized = (
                str(forbidden).replace("\\", "/").lower()
            )

            if normalized == forbidden_normalized:
                return False

        if not contract.allowed_files:
            return True

        allowed = {
            str(item).replace("\\", "/").lower()
            for item in contract.allowed_files
        }

        return normalized in allowed

    def check_permission(
        self,
        permission: str,
        task_id: Optional[str] = None,
    ) -> bool:
        contract = self.get_contract(task_id)

        requested = str(permission).strip().lower()

        permissions = {
            str(item).strip().lower()
            for item in contract.permissions
        }

        return requested in permissions

    def require_file_scope(
        self,
        file_path: str,
        task_id: Optional[str] = None,
    ) -> None:
        if not self.check_file_scope(file_path, task_id):
            raise PermissionError(
                f"File outside development contract scope: {file_path}"
            )

    def require_permission(
        self,
        permission: str,
        task_id: Optional[str] = None,
    ) -> None:
        if not self.check_permission(permission, task_id):
            raise PermissionError(
                f"Permission not granted by development contract: {permission}"
            )

    # ------------------------------------------------------------------
    # CONTEXT
    # ------------------------------------------------------------------

    def build_context(
        self,
        task_id: Optional[str] = None,
        files: Optional[Sequence[str]] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        contract = self.get_contract(task_id)

        filtered_files = self.context_filter.filter_files(
            files or [],
            contract.allowed_files,
        )

        context: Dict[str, Any] = {
            "task": {
                "task_id": contract.task_id,
                "title": contract.title,
                "goal": contract.goal,
                "scope": list(contract.scope),
                "requirements": list(contract.requirements),
                "success_criteria": list(contract.success_criteria),
            },
            "files": filtered_files,
        }

        if extra_context:
            context["extra"] = extra_context

        return self.context_filter.sanitize_context(context)

    # ------------------------------------------------------------------
    # CHANGE REQUEST
    # ------------------------------------------------------------------

    def create_change_request(
        self,
        reason: str,
        requested_changes: Sequence[str],
        task_id: Optional[str] = None,
    ) -> ChangeRequest:
        contract = self.get_contract(task_id)

        request = ChangeRequest(
            request_id=_new_id("change"),
            task_id=contract.task_id,
            reason=str(reason),
            requested_changes=[str(x) for x in requested_changes],
        )

        self.change_requests[request.request_id] = request

        self._record(
            contract.task_id,
            "CHANGE_REQUEST_CREATED",
            {
                "request_id": request.request_id,
                "reason": request.reason,
            },
        )

        return request

    def resolve_change_request(
        self,
        request_id: str,
        approved: bool,
        note: str = "",
    ) -> ChangeRequest:
        if request_id not in self.change_requests:
            raise KeyError(f"Unknown request_id: {request_id}")

        request = self.change_requests[request_id]

        if request.status != ChangeRequestStatus.PENDING:
            raise RuntimeError(
                f"Change request already resolved: {request.status.value}"
            )

        request.status = (
            ChangeRequestStatus.APPROVED
            if approved
            else ChangeRequestStatus.REJECTED
        )

        request.resolved_at = _now()
        request.resolution_note = str(note)

        self._record(
            request.task_id,
            "CHANGE_REQUEST_RESOLVED",
            {
                "request_id": request.request_id,
                "approved": bool(approved),
                "note": str(note),
            },
        )

        return request

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------

    def status(
        self,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        contract = self.get_contract(task_id)

        pending_changes = sum(
            1
            for request in self.change_requests.values()
            if request.task_id == contract.task_id
            and request.status == ChangeRequestStatus.PENDING
        )

        return {
            "module": "development_support",
            "version": VERSION,
            "task_id": contract.task_id,
            "title": contract.title,
            "goal": contract.goal,
            "status": contract.status.value,
            "contract_version": contract.version,
            "pending_change_requests": pending_changes,
            "history_entries": len(
                [
                    item
                    for item in self.history
                    if item.task_id == contract.task_id
                ]
            ),
        }

    # ------------------------------------------------------------------
    # SELF CHECK
    # ------------------------------------------------------------------

    def self_check(self) -> Dict[str, Any]:
        """
        Kiểm tra core Development Support.

        Quan trọng:
        Không dùng all() trên toàn bộ results vì module/version
        là metadata dạng string, không phải test boolean.
        """

        results: Dict[str, Any] = {
            "module": "development_support",
            "version": VERSION,
            "contract_creation": False,
            "contract_lock": False,
            "scope_guard": False,
            "context_filter": False,
            "change_request": False,
            "history": False,
            "passed": False,
        }

        test_keys = (
            "contract_creation",
            "contract_lock",
            "scope_guard",
            "context_filter",
            "change_request",
            "history",
        )

        try:
            support = DevelopmentSupport()

            contract = support.create_contract(
                title="Self Check",
                goal="Verify Development Support core",
                scope=["development_support.py"],
                allowed_files=["development_support.py"],
                forbidden_files=[".env"],
                permissions=["read_project"],
                requirements=["basic contract lifecycle"],
                success_criteria=["all core checks pass"],
            )

            results["contract_creation"] = (
                contract.status == ContractStatus.DRAFT
                and contract.task_id in support.contracts
            )

            support.approve_contract(contract.task_id)
            support.lock_contract(contract.task_id)

            results["contract_lock"] = (
                support.get_contract(contract.task_id).status
                == ContractStatus.LOCKED
            )

            results["scope_guard"] = (
                support.check_file_scope(
                    "development_support.py",
                    contract.task_id,
                )
                and not support.check_file_scope(
                    ".env",
                    contract.task_id,
                )
            )

            context = support.build_context(
                task_id=contract.task_id,
                files=[
                    "development_support.py",
                    ".env",
                ],
                extra_context={
                    "note": "api_key=SECRET_VALUE",
                },
            )

            results["context_filter"] = (
                ".env" not in context["files"]
                and "[REDACTED]" in context["extra"]["note"]
            )

            request = support.create_change_request(
                reason="Self check",
                requested_changes=["test change request"],
                task_id=contract.task_id,
            )

            support.resolve_change_request(
                request.request_id,
                approved=True,
                note="Self check approved",
            )

            results["change_request"] = (
                support.change_requests[
                    request.request_id
                ].status
                == ChangeRequestStatus.APPROVED
            )

            results["history"] = (
                len(support.get_history(contract.task_id)) >= 5
            )

            # CHỈ kiểm tra các field test thực sự là boolean.
            # Không đưa "module" và "version" vào phép all().
            results["passed"] = all(
                results[key] is True
                for key in test_keys
            )

        except Exception as exc:
            results["error"] = f"{type(exc).__name__}: {exc}"
            results["passed"] = False

        return results


# ----------------------------------------------------------------------
# MODULE-LEVEL API
# ----------------------------------------------------------------------

_SUPPORT_SINGLETON: Optional[DevelopmentSupport] = None


def get_support() -> DevelopmentSupport:
    global _SUPPORT_SINGLETON

    if _SUPPORT_SINGLETON is None:
        _SUPPORT_SINGLETON = DevelopmentSupport()

    return _SUPPORT_SINGLETON


def create_development_support() -> DevelopmentSupport:
    return DevelopmentSupport()


def status() -> Dict[str, Any]:
    support = get_support()

    if support.active_task_id is None:
        return {
            "module": "development_support",
            "version": VERSION,
            "active_task_id": None,
            "status": "IDLE",
        }

    return support.status()


def self_check() -> Dict[str, Any]:
    return DevelopmentSupport().self_check()


if __name__ == "__main__":
    print(
        json.dumps(
            self_check(),
            ensure_ascii=False,
            indent=2,
        )
    )