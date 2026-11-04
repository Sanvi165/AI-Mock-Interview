"""Pydantic models for sign up and login."""
import re

from pydantic import BaseModel, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{2,40}$")


class RegisterRequest(BaseModel):
    """Sign up: username, email and password."""

    username: str = Field(min_length=2, max_length=40)
    email: str
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def check_username(cls, value: str) -> str:
        value = value.strip()
        if not USERNAME_PATTERN.match(value):
            raise ValueError(
                "Username must be 2-40 characters: letters, numbers, dots, dashes or underscores."
            )
        return value

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) > 254 or not EMAIL_PATTERN.match(value):
            raise ValueError("Enter a valid email address.")
        return value


class LoginRequest(BaseModel):
    """Log in with either the username or the email, plus the password."""

    identifier: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("identifier", mode="before")
    @classmethod
    def strip_identifier(cls, value):
        return value.strip() if isinstance(value, str) else value


class UserOut(BaseModel):
    id: int
    username: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut