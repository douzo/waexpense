import json
import logging
import os

import boto3
from mangum import Mangum

from app.main import app


logger = logging.getLogger(__name__)

_mangum_handler = Mangum(app)
_lambda_client = boto3.client("lambda")
_env_manager_function_name = os.getenv("ENV_MANAGER_FUNCTION_NAME")


def lambda_handler(event, context):
    if _env_manager_function_name:
        try:
            _lambda_client.invoke(
                FunctionName=_env_manager_function_name,
                InvocationType="Event",
                Payload=json.dumps({"action": "wakeOnDemand"}),
            )
        except Exception as exc:  # pragma: no cover - best-effort
            logger.warning("Failed to invoke env manager from API: %s", exc)

    return _mangum_handler(event, context)
