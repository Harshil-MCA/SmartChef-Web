from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class FirebaseIdentityError(Exception):
    pass


def verify_id_token(id_token: str) -> dict[str, str]:
    api_key = getattr(settings, "FIREBASE_WEB_API_KEY", "").strip()
    if not api_key:
        raise FirebaseIdentityError("Firebase authentication is not configured on the server.")
    if not id_token.strip():
        raise FirebaseIdentityError("Firebase ID token is required.")

    request = Request(
        "https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=" + api_key,
        data=json.dumps({"idToken": id_token}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise FirebaseIdentityError("Firebase identity verification failed.") from error

    users = payload.get("users") if isinstance(payload, dict) else None
    identity = users[0] if isinstance(users, list) and users and isinstance(users[0], dict) else None
    if not identity or not identity.get("localId") or not identity.get("email"):
        raise FirebaseIdentityError("Firebase identity response was incomplete.")
    return {
        "firebase_uid": str(identity["localId"]),
        "email": str(identity["email"]).lower().strip(),
        "display_name": str(identity.get("displayName") or "").strip(),
        "photo_url": str(identity.get("photoUrl") or "").strip(),
    }
