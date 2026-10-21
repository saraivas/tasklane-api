from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import (
    ALGORITHM,
    SECRET_KEY,
    SESSION_MAX_LIFETIME_DAYS,
)
from app.core.security import decode_token
from app.models.user import User


def test_register_creates_user(client):
    response = client.post("/auth/register", json={
        "email": "teste@example.com",
        "password": "senha123",
    })

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "teste@example.com"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_rejects_duplicate_email(client):
    client.post("/auth/register", json={
        "email": "duplicado@example.com",
        "password": "senha123",
    })

    response = client.post("/auth/register", json={
        "email": "duplicado@example.com",
        "password": "outrasenha",
    })

    assert response.status_code == 400


def test_login_succeeds_with_correct_credentials(client):
    client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "senha123",
    })

    response = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "senha123",
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_fails_with_wrong_password(client):
    client.post("/auth/register", json={
        "email": "senhaerrada@example.com",
        "password": "senhacerta",
    })

    response = client.post("/auth/login", json={
        "email": "senhaerrada@example.com",
        "password": "senhaerrada",
    })

    assert response.status_code == 401


# --- /auth/refresh -----------------------------------------------------------


def _login(client, email="refresh@example.com"):
    user = client.post("/auth/register", json={
        "email": email,
        "password": "senha123",
    }).json()
    tokens = client.post("/auth/login", json={
        "email": email,
        "password": "senha123",
    }).json()
    return user["id"], tokens


def _craft_refresh_token(user_id, *, exp, auth_time, token_type="refresh"):
    """Sign a token with the app's own key, to test states login can't produce."""
    payload = {"sub": user_id, "exp": exp, "type": token_type}
    if auth_time is not None:
        payload["auth_time"] = auth_time
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _ts(dt):
    return int(dt.timestamp())


def test_login_response_is_not_cacheable(client):
    client.post("/auth/register", json={"email": "nc@example.com", "password": "senha123"})
    response = client.post("/auth/login", json={"email": "nc@example.com", "password": "senha123"})

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"


def test_refresh_returns_new_access_and_refresh_tokens(client):
    _, tokens = _login(client)

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert "refresh_token" in data
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"

    # The new access token works on a protected route...
    tasks = client.get("/tasks", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert tasks.status_code == 200
    # ...and the new refresh token can be used again.
    again = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert again.status_code == 200


def test_refresh_rejects_token_sent_in_query_string(client):
    _, tokens = _login(client)

    response = client.post(f"/auth/refresh?refresh_token={tokens['refresh_token']}")

    assert response.status_code == 422


def test_refresh_rejects_access_token(client):
    _, tokens = _login(client)

    response = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})

    assert response.status_code == 401


def test_refresh_rejects_garbage_token(client):
    response = client.post("/auth/refresh", json={"refresh_token": "token.invalido.aqui"})

    assert response.status_code == 401


def test_refresh_rejects_expired_token(client):
    user_id, _ = _login(client)
    now = datetime.now(timezone.utc)
    expired = _craft_refresh_token(
        user_id,
        exp=now - timedelta(minutes=1),
        auth_time=_ts(now - timedelta(days=1)),
    )

    response = client.post("/auth/refresh", json={"refresh_token": expired})

    assert response.status_code == 401


def test_refresh_rejects_token_without_auth_time(client):
    user_id, _ = _login(client)
    legacy = _craft_refresh_token(
        user_id,
        exp=datetime.now(timezone.utc) + timedelta(days=1),
        auth_time=None,
    )

    response = client.post("/auth/refresh", json={"refresh_token": legacy})

    assert response.status_code == 401


def test_refresh_rejects_session_older_than_the_absolute_limit(client):
    user_id, _ = _login(client)
    now = datetime.now(timezone.utc)
    old_session = _craft_refresh_token(
        user_id,
        exp=now + timedelta(days=1),
        auth_time=_ts(now - timedelta(days=SESSION_MAX_LIFETIME_DAYS + 1)),
    )

    response = client.post("/auth/refresh", json={"refresh_token": old_session})

    assert response.status_code == 401


def test_refresh_rejects_token_of_deleted_user(client, db_session):
    user_id, tokens = _login(client, email="gone@example.com")
    db_session.query(User).filter(User.email == "gone@example.com").delete()
    db_session.commit()

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 401


def test_refresh_slides_the_expiry_window(client):
    user_id, _ = _login(client)
    now = datetime.now(timezone.utc)
    old_exp = now + timedelta(days=1)
    token = _craft_refresh_token(
        user_id,
        exp=old_exp,
        auth_time=_ts(now - timedelta(days=10)),
    )

    response = client.post("/auth/refresh", json={"refresh_token": token})

    assert response.status_code == 200
    new_exp = decode_token(response.json()["refresh_token"])["exp"]
    assert new_exp > _ts(old_exp)
    assert new_exp - _ts(now) > 6 * 24 * 3600


def test_refresh_keeps_the_original_login_time(client):
    _, tokens = _login(client)
    original = decode_token(tokens["refresh_token"])["auth_time"]

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    renewed = decode_token(response.json()["refresh_token"])
    assert renewed["auth_time"] == original


def test_refresh_expiry_never_passes_the_absolute_limit(client):
    user_id, _ = _login(client)
    now = datetime.now(timezone.utc)
    auth_time = _ts(now - timedelta(days=SESSION_MAX_LIFETIME_DAYS - 1))
    token = _craft_refresh_token(
        user_id,
        exp=now + timedelta(days=1),
        auth_time=auth_time,
    )

    response = client.post("/auth/refresh", json={"refresh_token": token})

    assert response.status_code == 200
    new_exp = decode_token(response.json()["refresh_token"])["exp"]
    assert new_exp == auth_time + SESSION_MAX_LIFETIME_DAYS * 24 * 3600
