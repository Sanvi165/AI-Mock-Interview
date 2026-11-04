"""Sign up, log in, log out and the current-user dependency used by other routes.

Set REQUIRE_LOGIN=false in backend/.env to run without a login page (everyone uses one
shared "guest" account). Leave it unset or "true" for normal login behaviour.
"""
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from app.database import repositories
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])

TOKEN_LIFETIME_DAYS = 30
GUEST_USERNAME = "guest"
GUEST_EMAIL = "guest@local.invalid"


def _login_required() -> bool:
    return os.getenv("REQUIRE_LOGIN", "true").strip().lower() != "false"


def _guest_user() -> dict:
    user = repositories.get_user_by_username(GUEST_USERNAME)
    if user is None:
        try:
            # "!disabled" is not a valid password hash, so nobody can log in as guest.
            user = repositories.create_user(GUEST_USERNAME, GUEST_EMAIL, "!disabled")
        except sqlite3.IntegrityError:
            user = repositories.get_user_by_email(GUEST_EMAIL)
    return user


def _extract_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    return token


def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """FastAPI dependency: returns the logged-in user or raises 401."""
    if not authorization and not _login_required():
        return _guest_user()

    token = _extract_token(authorization)
    token_hash = auth_service.hash_token(token)
    user = repositories.get_user_by_token_hash(token_hash)
    if user is None:
        raise HTTPException(status_code=401, detail="Your session has expired. Please log in again.")

    try:
        issued = datetime.fromisoformat(user["token_created_at"])
    except ValueError:
        issued = None
    if issued is None or datetime.now(timezone.utc) - issued > timedelta(days=TOKEN_LIFETIME_DAYS):
        repositories.delete_token(token_hash)
        raise HTTPException(status_code=401, detail="Your session has expired. Please log in again.")
    return user


def _issue_token(user: dict) -> AuthResponse:
    token = auth_service.new_token()
    repositories.save_token(auth_service.hash_token(token), user["id"])
    return AuthResponse(token=token, user=UserOut(**user))


@router.post("/register", response_model=AuthResponse, status_code=201)
def sign_up(payload: RegisterRequest) -> AuthResponse:
    """Sign up with username, email and password. The user is logged in straight away."""
    if repositories.get_user_by_email(payload.email):
        raise HTTPException(
            status_code=409, detail="An account with this email already exists. Please log in."
        )
    if repositories.get_user_by_username(payload.username):
        raise HTTPException(
            status_code=409, detail="This username is already taken. Please choose another."
        )
    try:
        user = repositories.create_user(
            payload.username, payload.email, auth_service.hash_password(payload.password)
        )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail="An account with this email already exists. Please log in."
        )
    return _issue_token(user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    """Log in with a username OR an email, plus the password."""
    identifier = payload.identifier
    if "@" in identifier:
        user = repositories.get_user_by_email(identifier.lower())
    else:
        user = repositories.get_user_by_username(identifier)

    if user is None or not auth_service.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username/email or password.")
    return _issue_token(user)


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)) -> UserOut:
    return UserOut(**user)


@router.post("/logout")
def logout(
    authorization: Optional[str] = Header(default=None),
    user: dict = Depends(get_current_user),
) -> dict:
    repositories.delete_token(auth_service.hash_token(_extract_token(authorization)))
    return {"status": "logged out"}