from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
import ast
import py_compile
import sys


BASE_DIR = Path(__file__).resolve().parent
TARGET = BASE_DIR / "world_model.py"


WORLD_MODEL_CODE = r'''from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


WORLD_MODEL_VERSION = "P5-1.0"


@dataclass
class WorldState:
    """
    Trạng thái thế giới hiện tại của MINH MINI.

    World Model chỉ quản lý STATE.
    Không thực thi tool, không gọi Ollama, không route intent.
    """

    current_time: Optional[str] = None
    current_date: Optional[str] = None

    location: Optional[str] = None

    active_goal: Optional[Dict[str, Any]] = None
    active_task: Optional[Dict[str, Any]] = None

    known_facts: Dict[str, Any] = field(default_factory=dict)
    environment_state: Dict[str, Any] = field(default_factory=dict)

    last_observation: Optional[Dict[str, Any]] = None
    last_update: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


class WorldModel:
    """
    P5-1 World Model Core.

    Responsibilities:
    - create/read/update world state
    - record observations
    - create immutable snapshots
    - validate state structure

    Non-responsibilities:
    - routing
    - planning
    - execution
    - web
    - memory persistence
    - Ollama
    """

    def __init__(self) -> None:
        self.state = WorldState()
        self._refresh_timestamp()

    # ============================================================
    # INTERNAL
    # ============================================================

    def _refresh_timestamp(self) -> None:
        self.state.last_update = datetime.now().isoformat()

    # ============================================================
    # STATE
    # ============================================================

    def get_state(self) -> Dict[str, Any]:
        return deepcopy(asdict(self.state))

    def update_state(
        self,
        updates: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}

        if updates:
            payload.update(updates)

        payload.update(kwargs)

        for key, value in payload.items():
            if not hasattr(self.state, key):
                raise KeyError(f"Unknown world state field: {key}")

            setattr(self.state, key, deepcopy(value))

        self._refresh_timestamp()

        return self.get_state()

    # ============================================================
    # GOAL / TASK
    # ============================================================

    def set_goal(
        self,
        goal: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        self.state.active_goal = deepcopy(goal)
        self._refresh_timestamp()
        return self.get_state()

    def set_task(
        self,
        task: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        self.state.active_task = deepcopy(task)
        self._refresh_timestamp()
        return self.get_state()

    # ============================================================
    # FACTS
    # ============================================================

    def set_fact(
        self,
        key: str,
        value: Any,
    ) -> Dict[str, Any]:
        normalized = str(key).strip()

        if not normalized:
            raise ValueError("fact key is required")

        self.state.known_facts[normalized] = deepcopy(value)
        self._refresh_timestamp()

        return self.get_state()

    def get_fact(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return deepcopy(
            self.state.known_facts.get(
                str(key).strip(),
                default,
            )
        )

    # ============================================================
    # ENVIRONMENT
    # ============================================================

    def set_environment(
        self,
        key: str,
        value: Any,
    ) -> Dict[str, Any]:
        normalized = str(key).strip()

        if not normalized:
            raise ValueError("environment key is required")

        self.state.environment_state[normalized] = deepcopy(value)
        self._refresh_timestamp()

        return self.get_state()

    # ============================================================
    # OBSERVATION
    # ============================================================

    def record_observation(
        self,
        observation: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(observation, dict):
            raise TypeError("observation must be a dict")

        self.state.last_observation = deepcopy(observation)
        self._refresh_timestamp()

        return self.get_state()

    # ============================================================
    # SNAPSHOT
    # ============================================================

    def snapshot(self) -> Dict[str, Any]:
        """
        Trả về snapshot độc lập.

        Thay đổi snapshot không được làm thay đổi state thật.
        """
        return deepcopy(asdict(self.state))

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate(self) -> Dict[str, Any]:
        required_fields = {
            "current_time",
            "current_date",
            "location",
            "active_goal",
            "active_task",
            "known_facts",
            "environment_state",
            "last_observation",
            "last_update",
            "metadata",
        }

        actual_fields = set(self.get_state().keys())

        missing = sorted(
            required_fields - actual_fields
        )

        extra = sorted(
            actual_fields - required_fields
        )

        valid = (
            not missing
            and not extra
            and isinstance(self.state.known_facts, dict)
            and isinstance(self.state.environment_state, dict)
            and isinstance(self.state.metadata, dict)
        )

        return {
            "valid": valid,
            "missing": missing,
            "extra": extra,
            "version": WORLD_MODEL_VERSION,
        }

    # ============================================================
    # STATUS
    # ============================================================

    def status(self) -> Dict[str, Any]:
        validation = self.validate()

        return {
            "module": "world_model",
            "version": WORLD_MODEL_VERSION,
            "valid": validation["valid"],
            "facts": len(self.state.known_facts),
            "environment_items": len(
                self.state.environment_state
            ),
            "has_goal": self.state.active_goal is not None,
            "has_task": self.state.active_task is not None,
            "has_observation": (
                self.state.last_observation is not None
            ),
        }


def create_world_model() -> WorldModel:
    return WorldModel()


def self_check() -> Dict[str, Any]:
    model = create_world_model()

    initial = model.get_state()

    if not isinstance(initial, dict):
        raise AssertionError("get_state() must return dict")

    model.set_fact(
        "learning",
        "Python",
    )

    if model.get_fact("learning") != "Python":
        raise AssertionError("fact storage failed")

    model.set_environment(
        "network",
        "online",
    )

    model.record_observation(
        {
            "source": "test",
            "success": True,
        }
    )

    model.set_goal(
        {
            "text": "test goal",
            "status": "active",
        }
    )

    model.set_task(
        {
            "name": "test task",
            "status": "running",
        }
    )

    snapshot = model.snapshot()

    if snapshot["known_facts"]["learning"] != "Python":
        raise AssertionError("snapshot fact missing")

    snapshot["known_facts"]["learning"] = "MUTATED"

    if model.get_fact("learning") != "Python":
        raise AssertionError(
            "snapshot mutated live world state"
        )

    validation = model.validate()

    if not validation["valid"]:
        raise AssertionError(
            "world model validation failed"
        )

    status = model.status()

    if status["valid"] is not True:
        raise AssertionError(
            "world model status invalid"
        )

    return {
        "module": "world_model",
        "version": WORLD_MODEL_VERSION,
        "state_creation": True,
        "state_update": True,
        "fact_storage": True,
        "environment_state": True,
        "observation": True,
        "snapshot": True,
        "snapshot_isolated": True,
        "validation": True,
        "passed": True,
    }


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            self_check(),
            ensure_ascii=False,
            indent=2,
        )
    )
'''


def backup_existing() -> None:
    if not TARGET.exists():
        return

    backup = TARGET.with_name(
        "world_model.py.before_p5_1"
    )

    if backup.exists():
        index = 1

        while True:
            candidate = TARGET.with_name(
                f"world_model.py.before_p5_1_{index}"
            )

            if not candidate.exists():
                backup = candidate
                break

            index += 1

    backup.write_text(
        TARGET.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    print(f"BACKUP CREATED: {backup}")


def compile_check() -> None:
    py_compile.compile(
        str(TARGET),
        doraise=True,
    )


def ast_check() -> None:
    source = TARGET.read_text(
        encoding="utf-8"
    )

    ast.parse(source, filename=str(TARGET))


def import_check() -> None:
    import importlib

    sys.path.insert(0, str(BASE_DIR))

    module = importlib.import_module(
        "world_model"
    )

    factory = getattr(
        module,
        "create_world_model",
        None,
    )

    self_check = getattr(
        module,
        "self_check",
        None,
    )

    if not callable(factory):
        raise RuntimeError(
            "create_world_model() missing"
        )

    if not callable(self_check):
        raise RuntimeError(
            "self_check() missing"
        )

    result = self_check()

    if not isinstance(result, dict):
        raise RuntimeError(
            "self_check() must return dict"
        )

    if result.get("passed") is not True:
        raise RuntimeError(
            "World Model self_check failed"
        )


def main() -> int:
    print("=" * 64)
    print("MINH MINI — P5-1 WORLD MODEL CORE PATCH")
    print("=" * 64)

    backup_existing()

    TARGET.write_text(
        WORLD_MODEL_CODE,
        encoding="utf-8",
    )

    print("WORLD MODEL WRITE : PASS")

    ast_check()
    print("AST               : PASS")

    compile_check()
    print("COMPILE            : PASS")

    import_check()
    print("IMPORT             : PASS")
    print("SELF CHECK         : PASS")

    print("=" * 64)
    print("P5-1 WORLD MODEL CORE: PASS")
    print("=" * 64)
    print(f"FILE: {TARGET}")
    print("MAIN.PY MODIFIED: NO")
    print("P4-5 TOUCHED: NO")
    print("P4-4 TOUCHED: NO")
    print("=" * 64)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
