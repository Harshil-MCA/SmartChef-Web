from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from django.conf import settings


class JWTError(Exception):
    pass


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _json_dumps(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def create_token(*, user_id: str, token_type: str, expires_in: timedelta, session_id: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_in).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    if session_id:
        payload["sid"] = str(session_id)
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url_encode(_json_dumps(header).encode("utf-8"))
    encoded_payload = _b64url_encode(_json_dumps(payload).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    encoded_signature = _b64url_encode(signature)
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise JWTError("Token format is invalid.") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    actual_signature = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise JWTError("Token signature is invalid.")

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise JWTError("Token payload is invalid.") from exc

    now = int(datetime.now(timezone.utc).timestamp())
    exp = int(payload.get("exp", 0))
    if exp <= now:
        raise JWTError("Token has expired.")

    if expected_type is not None and payload.get("type") != expected_type:
        raise JWTError("Token type is invalid.")

    if not payload.get("sub"):
        raise JWTError("Token subject missing.")

    return payload
