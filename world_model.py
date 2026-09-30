from __future__ import annotations

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
