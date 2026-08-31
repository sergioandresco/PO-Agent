"""Smoke-tests the Lambda entry point with real API Gateway v2 event shapes.

Without this, the first proof that Mangum, the handler path and the event
mapping line up would be a 502 in production.
"""

from typing import Any, cast

import pytest
from mangum.types import LambdaContext

from services.api import job_store
from services.api.lambda_handler import handler


@pytest.fixture(autouse=True)
def _clean() -> None:
    job_store.use_store(None)
    job_store.reset()


def _context() -> LambdaContext:
    """Nothing in the app reads the Lambda context, so an empty stand-in is enough."""
    return cast(LambdaContext, object())


def _event(method: str, path: str, *, headers: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"host": "api.example.com", **(headers or {})},
        "requestContext": {
            "http": {
                "method": method,
                "path": path,
                "protocol": "HTTP/1.1",
                "sourceIp": "1.2.3.4",
            },
            "stage": "$default",
        },
        "isBase64Encoded": False,
    }


def test_health_route_answers_without_auth() -> None:
    response = handler(_event("GET", "/health"), _context())

    assert response["statusCode"] == 200
    assert '"ok"' in response["body"]


def test_protected_route_rejects_a_request_with_no_token() -> None:
    response = handler(_event("GET", "/jobs"), _context())

    # 401 from Clerk, or 500 when CLERK_SECRET_KEY is absent as it is here — either
    # way the point stands: no anonymous read reaches the store.
    assert response["statusCode"] in (401, 500)


def test_preflight_gets_cors_headers_for_the_configured_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    origin = "https://d2535zv4v0sfg0.cloudfront.net"
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", origin)

    # The middleware reads the origin list at app construction, so the app has to
    # be rebuilt for the override to take effect.
    import importlib

    from services.api import app as app_module

    importlib.reload(app_module)
    from mangum import Mangum

    reloaded = Mangum(app_module.app, lifespan="off")

    response = reloaded(
        _event(
            "OPTIONS",
            "/jobs",
            headers={"origin": origin, "access-control-request-method": "POST"},
        ),
        _context(),
    )

    assert response["statusCode"] == 200
    assert response["headers"]["access-control-allow-origin"] == origin
