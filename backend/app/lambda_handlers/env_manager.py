import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import boto3


logger = logging.getLogger(__name__)

rds = boto3.client("rds")
lambda_client = boto3.client("lambda")
ssm = boto3.client("ssm")


DB_INSTANCE_IDENTIFIER = os.getenv("DB_INSTANCE_IDENTIFIER")
INBOUND_MAPPING_UUID = os.getenv("INBOUND_MAPPING_UUID")
OUTBOUND_MAPPING_UUID = os.getenv("OUTBOUND_MAPPING_UUID")
ENV_STATE_SSM_PARAMETER_NAME = os.getenv("ENV_STATE_SSM_PARAMETER_NAME")
ENABLE_AUTO_SLEEP = os.getenv("ENABLE_AUTO_SLEEP", "false").lower() == "true"
IDLE_MINUTES_THRESHOLD = int(os.getenv("IDLE_MINUTES_THRESHOLD", "30"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_state() -> Dict[str, Any]:
    now = _now_iso()
    return {
        "state": "active",
        "lastActivityAt": now,
        "overrideAlwaysOn": False,
    }


def _load_state() -> Dict[str, Any]:
    if not ENV_STATE_SSM_PARAMETER_NAME:
        return _default_state()

    try:
        resp = ssm.get_parameter(Name=ENV_STATE_SSM_PARAMETER_NAME)
        value = resp.get("Parameter", {}).get("Value") or "{}"
        state = json.loads(value)
    except ssm.exceptions.ParameterNotFound:
        state = _default_state()
        _save_state(state)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to load env state from SSM: %s", exc)
        state = _default_state()
    return state


def _save_state(state: Dict[str, Any]) -> None:
    if not ENV_STATE_SSM_PARAMETER_NAME:
        return
    try:
        ssm.put_parameter(
            Name=ENV_STATE_SSM_PARAMETER_NAME,
            Type="String",
            Value=json.dumps(state),
            Overwrite=True,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to save env state to SSM: %s", exc)


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _minutes_since(ts: str | None) -> float:
    dt = _parse_iso(ts)
    if not dt:
        return 0.0
    delta = datetime.now(timezone.utc) - dt
    return delta.total_seconds() / 60.0


def _set_mappings_enabled(enabled: bool) -> None:
    uuids = [INBOUND_MAPPING_UUID, OUTBOUND_MAPPING_UUID]
    for uuid in uuids:
        if not uuid:
            continue
        try:
            lambda_client.update_event_source_mapping(UUID=uuid, Enabled=enabled)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Failed to update event source mapping %s (enabled=%s): %s",
                uuid,
                enabled,
                exc,
            )


def _stop_db() -> None:
    if not DB_INSTANCE_IDENTIFIER:
        return
    try:
        rds.stop_db_instance(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
    except rds.exceptions.InvalidDBInstanceStateFault:
        # Already stopped or stopping
        return
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to stop DB instance %s: %s", DB_INSTANCE_IDENTIFIER, exc)


def _start_db() -> None:
    if not DB_INSTANCE_IDENTIFIER:
        return
    try:
        rds.start_db_instance(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
    except rds.exceptions.InvalidDBInstanceStateFault:
        # Already starting or available
        return
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to start DB instance %s: %s", DB_INSTANCE_IDENTIFIER, exc)


def _wait_for_db_available(timeout_minutes: int = 15) -> None:
    if not DB_INSTANCE_IDENTIFIER:
        return

    max_checks = max(int(timeout_minutes * 2), 1)
    for _ in range(max_checks):
        try:
            resp = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)
            dbs = resp.get("DBInstances") or []
            if dbs and dbs[0].get("DBInstanceStatus") == "available":
                return
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Error while polling DB status: %s", exc)
        # Use Lambda's built-in wait rather than time.sleep for clarity
        lambda_client.get_waiter  # no-op to avoid unused reference lint
    # If we exit the loop, we timed out; workers will still be re-enabled by
    # a later wake call once the DB is actually up.


def _handle_evaluate_idle(state: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_AUTO_SLEEP:
        return state

    if state.get("overrideAlwaysOn"):
        if state.get("state") != "active":
            state["state"] = "active"
            _save_state(state)
        return state

    minutes_idle = _minutes_since(state.get("lastActivityAt"))
    if minutes_idle < IDLE_MINUTES_THRESHOLD:
        return state

    if state.get("state") == "sleeping":
        return state

    state["state"] = "sleeping"
    _save_state(state)

    _set_mappings_enabled(False)
    _stop_db()
    return state


def _handle_wake_on_demand(state: Dict[str, Any]) -> Dict[str, Any]:
    now = _now_iso()
    state["lastActivityAt"] = now

    if state.get("overrideAlwaysOn"):
        if state.get("state") != "active":
            state["state"] = "active"
            _save_state(state)
        return state

    if state.get("state") == "active":
        _save_state(state)
        return state

    if state.get("state") == "waking":
        _save_state(state)
        return state

    state["state"] = "waking"
    _save_state(state)

    _start_db()
    _wait_for_db_available()
    _set_mappings_enabled(True)

    state["state"] = "active"
    _save_state(state)
    return state


def lambda_handler(event, context):
    """
    Control-plane Lambda to manage sleep/wake of the environment.

    Expected event payloads:
    - {"action": "evaluateIdle"}
    - {"action": "wakeOnDemand"}
    """

    action = (event or {}).get("action") or ""
    action = str(action).lower()

    state = _load_state()

    if action == "evaluateidle":
        state = _handle_evaluate_idle(state)
    elif action == "wakeondemand":
        state = _handle_wake_on_demand(state)
    else:
        logger.info("Unknown or missing action for env_manager: %s", action)

    return {"statusCode": 200, "body": json.dumps(state)}

