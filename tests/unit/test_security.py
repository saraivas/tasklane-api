from datetime import datetime, timedelta, timezone

from app.core.config import SESSION_MAX_LIFETIME_DAYS
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    session_has_expired,
)


def test_hash_password_is_not_plain_text():
    hashed = hash_password("minhasenha123")
    assert hashed != "minhasenha123"


def test_verify_password_succeeds_with_correct_password():
    hashed = hash_password("minhasenha123")
    assert verify_password("minhasenha123", hashed) is True


def test_verify_password_fails_with_wrong_password():
    hashed = hash_password("minhasenha123")
    assert verify_password("senhaerrada", hashed) is False


def test_access_token_can_be_decoded():
    token = create_access_token("user-123")
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_refresh_token_has_correct_type():
    token = create_refresh_token("user-123")
    payload = decode_token(token)

    assert payload["type"] == "refresh"


def test_decode_invalid_token_returns_none():
    payload = decode_token("token.invalido.aqui")
    assert payload is None


def test_refresh_token_carries_login_time_and_issue_time():
    before = int(datetime.now(timezone.utc).timestamp())
    payload = decode_token(create_refresh_token("user-123"))

    assert payload["auth_time"] >= before
    assert payload["iat"] >= before


def test_refresh_token_keeps_the_login_time_it_is_given():
    auth_time = int((datetime.now(timezone.utc) - timedelta(days=3)).timestamp())
    payload = decode_token(create_refresh_token("user-123", auth_time=auth_time))

    assert payload["auth_time"] == auth_time


def test_refresh_token_expiry_is_capped_by_the_session_limit():
    now = datetime.now(timezone.utc)
    auth_time = int((now - timedelta(days=SESSION_MAX_LIFETIME_DAYS - 1)).timestamp())
    payload = decode_token(create_refresh_token("user-123", auth_time=auth_time))

    assert payload["exp"] == auth_time + SESSION_MAX_LIFETIME_DAYS * 24 * 3600


def test_session_has_expired_only_after_the_limit():
    now = datetime.now(timezone.utc)
    inside = int((now - timedelta(days=SESSION_MAX_LIFETIME_DAYS - 1)).timestamp())
    outside = int((now - timedelta(days=SESSION_MAX_LIFETIME_DAYS + 1)).timestamp())

    assert session_has_expired(inside) is False
    assert session_has_expired(outside) is True
