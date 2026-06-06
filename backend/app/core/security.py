"""
Local-first security for Project Capsule.

Philosophy:
  Capsule is a LOCAL-FIRST tool. It runs on the user's machine.
  There is no multi-tenant auth, no JWT complexity, no session management.

  Security model:
  1. Bind to 127.0.0.1 only (no external exposure)
  2. Optional shared API key between extension ↔ backend (X-Capsule-Key header)
  3. In development mode (CAPSULE_API_KEY=""), auth is skipped entirely

  If a user wants to expose Capsule to a network, they set CAPSULE_API_KEY
  to a secret value in .env and distribute it to trusted clients only.
"""
from fastapi import Request, HTTPException, status
from app.core.config import settings


def verify_capsule_key(request: Request) -> None:
    """
    FastAPI dependency that validates the X-Capsule-Key header.
    Skipped entirely in development mode (CAPSULE_API_KEY is empty).
    """
    # Development mode: no auth required
    if not settings.CAPSULE_API_KEY:
        return

    api_key = request.headers.get("X-Capsule-Key", "")
    if api_key != settings.CAPSULE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Capsule-Key header.",
        )
