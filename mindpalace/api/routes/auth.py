from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any

import bcrypt
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
    RegistrationCredential,
    AuthenticationCredential,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier

from mindpalace.config import settings
from mindpalace.db import get_db, User, ApiKey, WebAuthnCredential

router = APIRouter(prefix="/api/auth")

# ── Token helpers ───────────────────────────────────
# Token format: user_id:timestamp:signature

_TOKEN_TTL = 30 * 24 * 3600  # 30 days


def _sign_token(user_id: str, issued_at: float) -> str:
    payload = f"{user_id}:{issued_at}"
    sig = hmac.new(settings.auth_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_token(token: str) -> str | None:
    """Verify token and return user_id, or None if invalid."""
    parts = token.split(":")
    if len(parts) != 3:
        return None
    user_id, issued_at_str, sig = parts
    try:
        issued_at = float(issued_at_str)
    except ValueError:
        return None
    if time.time() - issued_at > _TOKEN_TTL:
        return None
    expected = hmac.new(settings.auth_secret.encode(), f"{user_id}:{issued_at_str}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return user_id


def _get_user_id_from_request(request: Request) -> str:
    """Extract and verify user_id from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = verify_token(auth[7:])
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


# ── Registration ────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None


@router.post("/register")
def register(req: RegisterRequest):
    if not settings.auth_secret:
        raise HTTPException(status_code=503, detail="AUTH_SECRET not configured")
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    db = next(get_db())
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user = User(
        username=req.username,
        password_hash=password_hash,
        display_name=req.display_name or req.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = _sign_token(user.id, time.time())
    return {"token": token, "user_id": user.id, "username": user.username}


# ── Password login ──────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    if not settings.auth_secret:
        raise HTTPException(status_code=503, detail="AUTH_SECRET not configured")

    db = next(get_db())
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not bcrypt.checkpw(req.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _sign_token(user.id, time.time())
    return {"token": token, "user_id": user.id, "username": user.username}


@router.get("/check")
def check_auth(request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {"status": "ok", "user_id": user.id, "username": user.username}


# ── API Key management ──────────────────────────────

class CreateApiKeyRequest(BaseModel):
    label: str = "default"


@router.post("/api-keys")
def create_api_key(req: CreateApiKeyRequest, request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    api_key = ApiKey(user_id=user_id, label=req.label)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return {"id": api_key.id, "key": api_key.key, "label": api_key.label, "created_at": api_key.created_at.isoformat()}


@router.get("/api-keys")
def list_api_keys(request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    keys = db.query(ApiKey).filter(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc()).all()
    return [
        {"id": k.id, "key_preview": k.key[:8] + "...", "label": k.label, "created_at": k.created_at.isoformat()}
        for k in keys
    ]


@router.delete("/api-keys/{key_id}")
def delete_api_key(key_id: str, request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == user_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(key)
    db.commit()
    return {"deleted": key_id}


# ── WebAuthn config ─────────────────────────────────

_RP_ID = os.environ.get("WEBAUTHN_RP_ID", "localhost")
_RP_NAME = "MindPalace"
_ORIGIN = os.environ.get("WEBAUTHN_ORIGIN", "http://localhost:8080")
_challenges: dict[str, bytes] = {}


# ── WebAuthn Registration ──────────────────────────

@router.post("/webauthn/register/begin")
def webauthn_register_begin(request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401)

    existing = db.query(WebAuthnCredential).filter(WebAuthnCredential.user_id == user_id).all()
    exclude = [{"id": bytes.fromhex(c.credential_id), "type": "public-key"} for c in existing]

    options = generate_registration_options(
        rp_id=_RP_ID,
        rp_name=_RP_NAME,
        user_id=user.id.encode(),
        user_name=user.username,
        user_display_name=user.display_name or user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
    )

    _challenges[f"register:{user_id}"] = options.challenge
    return Response(content=options_to_json(options), media_type="application/json")


class WebAuthnRegisterComplete(BaseModel):
    credential: dict[str, Any]


@router.post("/webauthn/register/complete")
def webauthn_register_complete(request: Request, body: WebAuthnRegisterComplete):
    user_id = _get_user_id_from_request(request)
    challenge = _challenges.pop(f"register:{user_id}", None)
    if challenge is None:
        raise HTTPException(status_code=400, detail="No registration in progress")

    try:
        credential = RegistrationCredential.model_validate(body.credential)
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=_RP_ID,
            expected_origin=_ORIGIN,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    db = next(get_db())
    cred = WebAuthnCredential(
        user_id=user_id,
        credential_id=verification.credential_id.hex(),
        public_key=verification.credential_public_key.hex(),
        sign_count=verification.sign_count,
    )
    db.add(cred)
    db.commit()
    return {"status": "registered"}


# ── WebAuthn Authentication ─────────────────────────

@router.post("/webauthn/login/begin")
def webauthn_login_begin():
    db = next(get_db())
    creds = db.query(WebAuthnCredential).all()
    if not creds:
        raise HTTPException(status_code=404, detail="No passkeys registered")

    allow = [{"id": bytes.fromhex(c.credential_id), "type": "public-key"} for c in creds]

    options = generate_authentication_options(
        rp_id=_RP_ID,
        allow_credentials=allow,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    _challenges["login"] = options.challenge
    return Response(content=options_to_json(options), media_type="application/json")


class WebAuthnLoginComplete(BaseModel):
    credential: dict[str, Any]


@router.post("/webauthn/login/complete")
def webauthn_login_complete(body: WebAuthnLoginComplete):
    challenge = _challenges.pop("login", None)
    if challenge is None:
        raise HTTPException(status_code=400, detail="No authentication in progress")

    db = next(get_db())
    try:
        credential = AuthenticationCredential.model_validate(body.credential)
        cred_id_hex = credential.raw_id.hex() if credential.raw_id else ""
        stored = db.query(WebAuthnCredential).filter(WebAuthnCredential.credential_id == cred_id_hex).first()
        if not stored:
            raise ValueError("Unknown credential")

        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=_RP_ID,
            expected_origin=_ORIGIN,
            credential_public_key=bytes.fromhex(stored.public_key),
            credential_current_sign_count=stored.sign_count,
        )
        stored.sign_count = verification.new_sign_count
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    token = _sign_token(stored.user_id, time.time())
    return {"token": token, "user_id": stored.user_id}


@router.get("/webauthn/status")
def webauthn_status(request: Request):
    user_id = _get_user_id_from_request(request)
    db = next(get_db())
    count = db.query(WebAuthnCredential).filter(WebAuthnCredential.user_id == user_id).count()
    return {"registered": count > 0, "count": count}
