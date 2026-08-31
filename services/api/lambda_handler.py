"""API Gateway entry point.

Mangum adapts the ASGI app to the Lambda event shape, so the deployed API is the
exact same FastAPI application that runs locally — no parallel implementation,
no drift between what is tested and what is served (§10).

Secrets are resolved once per cold start, before the app handles anything.
"""

from services.secrets import load_secrets_into_env

load_secrets_into_env()

from mangum import Mangum  # noqa: E402  (must follow the secret load)

from services.api.app import app  # noqa: E402

handler = Mangum(app, lifespan="off")
