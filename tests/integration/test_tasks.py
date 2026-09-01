import uuid


def register_and_login(client, email, password="senha123"):
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_task_requires_authentication(client):
    response = client.post("/tasks", json={"title": "Sem token"})
    assert response.status_code == 401


def test_create_and_list_task(client):
    token = register_and_login(client, "dono@example.com")

    create_response = client.post(
        "/tasks",
        json={"title": "Minha tarefa"},
        headers=auth_headers(token),
    )
    assert create_response.status_code == 201

    list_response = client.get("/tasks", headers=auth_headers(token))
    assert list_response.status_code == 200
    tasks = list_response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Minha tarefa"


def test_user_cannot_see_another_users_task(client):
    token_a = register_and_login(client, "usuario_a@example.com")
    token_b = register_and_login(client, "usuario_b@example.com")

    create_response = client.post(
        "/tasks",
        json={"title": "Tarefa do usuário A"},
        headers=auth_headers(token_a),
    )
    task_id = create_response.json()["id"]

    response_as_b = client.get(f"/tasks/{task_id}", headers=auth_headers(token_b))
    assert response_as_b.status_code == 404


def test_get_nonexistent_task_returns_404(client):
    token = register_and_login(client, "usuario_c@example.com")

    nonexistent_task_id = uuid.uuid4()

    response = client.get(f"/tasks/{nonexistent_task_id}", headers=auth_headers(token))
    assert response.status_code == 404


def test_user_cannot_delete_another_users_task(client):
    token_a = register_and_login(client, "dono_real@example.com")
    token_b = register_and_login(client, "invasor@example.com")

    create_response = client.post(
        "/tasks",
        json={"title": "Tarefa protegida"},
        headers=auth_headers(token_a),
    )
    task_id = create_response.json()["id"]

    delete_response = client.delete(f"/tasks/{task_id}", headers=auth_headers(token_b))
    assert delete_response.status_code == 404

    check_response = client.get(f"/tasks/{task_id}", headers=auth_headers(token_a))
    assert check_response.status_code == 200


def test_task_list_only_shows_own_tasks(client):
    token_a = register_and_login(client, "usuario_x@example.com")
    token_b = register_and_login(client, "usuario_y@example.com")

    client.post("/tasks", json={"title": "Tarefa de X"}, headers=auth_headers(token_a))
    client.post("/tasks", json={"title": "Tarefa de Y - 1"}, headers=auth_headers(token_b))
    client.post("/tasks", json={"title": "Tarefa de Y - 2"}, headers=auth_headers(token_b))

    list_as_a = client.get("/tasks", headers=auth_headers(token_a)).json()
    list_as_b = client.get("/tasks", headers=auth_headers(token_b)).json()

    assert len(list_as_a) == 1
    assert len(list_as_b) == 2
