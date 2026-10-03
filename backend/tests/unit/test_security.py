"""Auth schema / security unit tests."""

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_token,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("SecurePass123!")
    assert verify_password("SecurePass123!", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    token = create_access_token("user-123", {"email": "a@b.com"})
    payload = validate_token(token, "access")
    assert payload["sub"] == "user-123"
    assert payload["email"] == "a@b.com"


def test_refresh_token_type():
    token = create_refresh_token("user-123")
    payload = validate_token(token, "refresh")
    assert payload["type"] == "refresh"
