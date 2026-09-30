from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional


STATE_MANAGER_VERSION = "P6-1.0"


class StateManager:
    """
    P6-1 State Manager Core.

    Responsibility:
    - Maintain application/session state.
    - Read and update state safely.
    - Maintain state history.
    - Provide isolated snapshots.
    - Reset state.
    - Validate state structure.

    Explicitly does NOT:
    - Execute actions.
    - Route requests.
    - Call Ollama.
    - Call Web.
    - Call external tools.
    - Modify World Model.
    """

    def __init__(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        history_limit: int = 50,
    ) -> None:
        self.version = STATE_MANAGER_VERSION
        self.history_limit = max(1, int(history_limit))

        self._state: Dict[str, Any] = deepcopy(
            initial_state if isinstance(initial_state, dict) else {}
        )

        self._history: List[Dict[str, Any]] = []

        self._refresh_timestamp()

    def _refresh_timestamp(self) -> None:
        self._state["last_update"] = datetime.now().isoformat()

    def get_state(self) -> Dict[str, Any]:
        """Return an isolated copy of the current state."""
        return deepcopy(self._state)

    def get(self, key: str, default: Any = None) -> Any:
        """Read one state value."""
        return deepcopy(self._state.get(key, default))

    def set(self, key: str, value: Any) -> Dict[str, Any]:
        """Set one state value and record the previous state."""
        self._record_history()

        self._state[key] = deepcopy(value)
        self._refresh_timestamp()

        return self.get_state()

    def update(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Update multiple state values atomically."""
        if not isinstance(values, dict):
            raise TypeError("values must be a dictionary")

        self._record_history()

        for key, value in values.items():
            self._state[key] = deepcopy(value)

        self._refresh_timestamp()

        return self.get_state()

    def remove(self, key: str) -> Dict[str, Any]:
        """Remove one state value if it exists."""
        self._record_history()

        self._state.pop(key, None)
        self._refresh_timestamp()

        return self.get_state()

    def reset(self, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reset current state and clear state history."""
        self._state = deepcopy(
            initial_state if isinstance(initial_state, dict) else {}
        )

        self._history.clear()
        self._refresh_timestamp()

        return self.get_state()

    def snapshot(self) -> Dict[str, Any]:
        """Return a deep isolated snapshot of current state."""
        return deepcopy(self._state)

    def history(self) -> List[Dict[str, Any]]:
        """Return isolated state history."""
        return deepcopy(self._history)

    def history_size(self) -> int:
        return len(self._history)

    def _record_history(self) -> None:
        """Store an isolated copy of the state before mutation."""
        self._history.append(deepcopy(self._state))

        if len(self._history) > self.history_limit:
            self._history = self._history[-self.history_limit :]

    def validate(self) -> Dict[str, Any]:
        """Validate State Manager integrity."""
        errors: List[str] = []

        if not isinstance(self._state, dict):
            errors.append("state_not_dict")

        if not isinstance(self._history, list):
            errors.append("history_not_list")

        if not isinstance(self.history_limit, int):
            errors.append("history_limit_not_int")

        if self.history_limit < 1:
            errors.append("history_limit_invalid")

        return {
            "valid": not errors,
            "errors": errors,
            "state_is_dict": isinstance(self._state, dict),
            "history_is_list": isinstance(self._history, list),
            "history_size": len(self._history),
            "history_limit": self.history_limit,
            "version": self.version,
        }

    def status(self) -> Dict[str, Any]:
        """Return operational status without exposing mutable internals."""
        return {
            "module": "state_manager",
            "version": self.version,
            "state_keys": list(self._state.keys()),
            "history_size": len(self._history),
            "history_limit": self.history_limit,
            "valid": self.validate()["valid"],
        }


def create_state_manager(
    initial_state: Optional[Dict[str, Any]] = None,
    history_limit: int = 50,
) -> StateManager:
    return StateManager(
        initial_state=initial_state,
        history_limit=history_limit,
    )


def self_check() -> Dict[str, Any]:
    """P6-1 Core self-check."""
    manager = create_state_manager(
        {
            "session": "P6-1",
            "counter": 0,
        }
    )

    initial = manager.get_state()

    state_creation = (
        isinstance(initial, dict)
        and initial.get("session") == "P6-1"
    )

    manager.set("counter", 1)

    state_update = manager.get("counter") == 1

    manager.update(
        {
            "mode": "test",
            "nested": {
                "value": 123,
            },
        }
    )

    multi_update = (
        manager.get("mode") == "test"
        and manager.get("nested", {}).get("value") == 123
    )

    snapshot = manager.snapshot()
    snapshot["nested"]["value"] = 999

    snapshot_isolated = (
        manager.get("nested", {}).get("value") == 123
    )

    history_present = manager.history_size() >= 2

    removed = manager.remove("mode")

    state_remove = "mode" not in removed

    manager.reset(
        {
            "reset": True,
        }
    )

    reset_ok = (
        manager.get("reset") is True
        and manager.history_size() == 0
    )

    validation = manager.validate()

    validation_ok = (
        validation.get("valid") is True
    )

    return {
        "module": "state_manager",
        "version": STATE_MANAGER_VERSION,
        "state_creation": state_creation,
        "state_update": state_update,
        "multi_update": multi_update,
        "snapshot_isolated": snapshot_isolated,
        "history": history_present,
        "remove": state_remove,
        "reset": reset_ok,
        "validation": validation_ok,
        "passed": all(
            [
                state_creation,
                state_update,
                multi_update,
                snapshot_isolated,
                history_present,
                state_remove,
                reset_ok,
                validation_ok,
            ]
        ),
    }


if __name__ == "__main__":
    import json

    result = self_check()

    print("=== P6-1 STATE MANAGER CORE ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["passed"]:
        print("P6-1 STATE MANAGER CORE PASS")
    else:
        print("P6-1 STATE MANAGER CORE FAIL")
        raise SystemExit(1)
