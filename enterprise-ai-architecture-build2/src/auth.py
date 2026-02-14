import os
import time
import requests
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Request

TENANT_ID = os.getenv("TENANT_ID")
API_AUDIENCE = os.getenv("API_AUDIENCE") or os.getenv("API_CLIENT_ID")

if not TENANT_ID or not API_AUDIENCE:
    # Fail fast if misconfigured
    raise RuntimeError("TENANT_ID and API_AUDIENCE (or API_CLIENT_ID) must be set")

ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"

# OpenID discovery gives us jwks_uri for signing keys
OIDC_CONFIG_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"


def _get_jwks_uri() -> str:
    r = requests.get(OIDC_CONFIG_URL, timeout=10)
    r.raise_for_status()
    return r.json()["jwks_uri"]


_JWKS_URI = _get_jwks_uri()
_JWK_CLIENT = PyJWKClient(_JWKS_URI)


def require_bearer_token(request: Request) -> dict:
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        signing_key = _JWK_CLIENT.get_signing_key_from_jwt(token).key

        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=API_AUDIENCE,
            issuer=ISSUER,
            options={
                "require": ["exp", "iss", "aud"],
            },
        )
        # Extra sanity check
        if claims.get("exp", 0) < int(time.time()):
            raise HTTPException(status_code=401, detail="Token expired")

        return claims

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Invalid issuer")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
