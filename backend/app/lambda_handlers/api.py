import json
import logging
import os

import boto3
from botocore.config import Config
from mangum import Mangum

from app.main import app


logger = logging.getLogger(__name__)

_mangum_handler = Mangum(app)
_lambda_client = boto3.client(
    "lambda",
    config=Config(connect_timeout=1, read_timeout=2, retries={"max_attempts": 0}),
)
_env_manager_function_name = os.getenv("ENV_MANAGER_FUNCTION_NAME")
_enable_auto_sleep = os.getenv("ENABLE_AUTO_SLEEP", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def lambda_handler(event, context):
    if _enable_auto_sleep and _env_manager_function_name:
        try:
            _lambda_client.invoke(
                FunctionName=_env_manager_function_name,
                InvocationType="Event",
                Payload=json.dumps({"action": "wakeOnDemand"}),
            )
        except Exception as exc:  # pragma: no cover - best-effort
            logger.warning("Failed to invoke env manager from API: %s", exc)

    return _mangum_handler(event, context)
