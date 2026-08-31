"""Pulls SecureString parameters out of SSM Parameter Store into the environment.

The pipeline and the Clerk verifier both read plain environment variables
(`LLM_API_KEY`, `CLERK_SECRET_KEY`) — that is what makes them runnable locally
from a .env.local with no AWS at all. In Lambda those values must not sit in the
function's environment, where anyone with console read access can see them, so
CDK instead injects the *parameter names* (`LLM_API_KEY_PARAM`, ...) and this
module resolves them once per cold start.

Parameter Store Standard tier is used rather than Secrets Manager: it is free,
and §12 rules out adding fixed-cost components without discussing them first.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("po_agent.secrets")

_SUFFIX = "_PARAM"
_loaded = False


def load_secrets_into_env(*, force: bool = False) -> None:
    """Resolves every `<NAME>_PARAM` variable into `<NAME>`. Idempotent.

    A value already present in `<NAME>` wins, so local development and tests are
    never touched. Missing parameters are logged and skipped rather than raised:
    the API Lambda needs Clerk but not the LLM key, and the worker the reverse.
    """
    global _loaded
    if _loaded and not force:
        return

    wanted = {
        key[: -len(_SUFFIX)]: value
        for key, value in os.environ.items()
        if key.endswith(_SUFFIX) and value and not os.environ.get(key[: -len(_SUFFIX)])
    }
    if not wanted:
        _loaded = True
        return

    import boto3

    client = boto3.client("ssm")
    response = client.get_parameters(Names=list(wanted.values()), WithDecryption=True)

    by_name = {param["Name"]: param["Value"] for param in response.get("Parameters", [])}
    for env_name, param_name in wanted.items():
        value = by_name.get(param_name)
        if value is None:
            logger.warning("SSM parameter %s not found; %s stays unset", param_name, env_name)
            continue
        os.environ[env_name] = value

    _loaded = True
