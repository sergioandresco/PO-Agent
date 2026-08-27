import os

from clerk_backend_api import (  # type: ignore[attr-defined]
    AuthenticateRequestOptions,
    authenticate_request,
)
from fastapi import HTTPException, Request


def _authorized_parties() -> list[str]:
    raw = os.environ.get("CLERK_AUTHORIZED_PARTIES", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def require_user_id(request: Request) -> str:
    """Verifies the Clerk session JWT and returns the userId (`sub` claim). Every
    handler that touches data must go through this — isolation is enforced here,
    not just in the frontend (§8)."""
    secret_key = os.environ.get("CLERK_SECRET_KEY")
    if not secret_key:
        raise HTTPException(status_code=500, detail="CLERK_SECRET_KEY is not configured")

    state = authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=secret_key,
            authorized_parties=_authorized_parties(),
            accepts_token=["session_token"],
        ),
    )
    if not state.is_signed_in or state.payload is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return str(state.payload["sub"])
