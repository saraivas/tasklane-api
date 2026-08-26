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
