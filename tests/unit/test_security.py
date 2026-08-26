from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
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
