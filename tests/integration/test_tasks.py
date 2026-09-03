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
    data = list_response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Minha tarefa"


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

    assert len(list_as_a["items"]) == 1
    assert len(list_as_b["items"]) == 2


def test_list_tasks_returns_paginated_response(client):
    token = register_and_login(client, "paginacao1@example.com")

    for i in range(5):
        client.post("/tasks", json={"title": f"Tarefa {i}"}, headers=auth_headers(token))

    response = client.get("/tasks", headers=auth_headers(token))
    data = response.json()

    assert response.status_code == 200
    assert "items" in data
    assert "total" in data
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["limit"] == 20
    assert len(data["items"]) == 5


def test_list_tasks_respects_limit(client):
    token = register_and_login(client, "paginacao2@example.com")

    for i in range(5):
        client.post("/tasks", json={"title": f"Tarefa {i}"}, headers=auth_headers(token))

    response = client.get("/tasks?limit=2", headers=auth_headers(token))
    data = response.json()

    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2


def test_list_tasks_second_page_returns_different_items(client):
    token = register_and_login(client, "paginacao3@example.com")

    for i in range(5):
        client.post("/tasks", json={"title": f"Tarefa {i}"}, headers=auth_headers(token))

    page1 = client.get("/tasks?page=1&limit=2", headers=auth_headers(token)).json()
    page2 = client.get("/tasks?page=2&limit=2", headers=auth_headers(token)).json()

    page1_ids = {item["id"] for item in page1["items"]}
    page2_ids = {item["id"] for item in page2["items"]}

    assert page1_ids.isdisjoint(page2_ids)


def test_list_tasks_rejects_limit_above_max(client):
    token = register_and_login(client, "paginacao4@example.com")

    response = client.get("/tasks?limit=101", headers=auth_headers(token))

    assert response.status_code == 422


def test_list_tasks_rejects_page_below_one(client):
    token = register_and_login(client, "paginacao5@example.com")

    response = client.get("/tasks?page=0", headers=auth_headers(token))

    assert response.status_code == 422


def test_update_task_changes_only_sent_fields(client):
    token = register_and_login(client, "patch_feliz@example.com")

    create_response = client.post(
        "/tasks",
        json={"title": "Titulo original", "description": "Descricao original"},
        headers=auth_headers(token),
    )
    task_id = create_response.json()["id"]

    update_response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "Titulo atualizado", "status": "done"},
        headers=auth_headers(token),
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == "Titulo atualizado"
    assert data["status"] == "done"
    assert data["description"] == "Descricao original"


def test_user_cannot_update_another_users_task(client):
    token_a = register_and_login(client, "dono_patch@example.com")
    token_b = register_and_login(client, "invasor_patch@example.com")

    create_response = client.post(
        "/tasks",
        json={"title": "Tarefa protegida"},
        headers=auth_headers(token_a),
    )
    task_id = create_response.json()["id"]

    update_response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "Tentativa de invasao"},
        headers=auth_headers(token_b),
    )
    assert update_response.status_code == 404

    check_response = client.get(f"/tasks/{task_id}", headers=auth_headers(token_a))
    assert check_response.json()["title"] == "Tarefa protegida"


def test_create_task_rejects_blank_title(client):
    token = register_and_login(client, "titulo_vazio_create@example.com")

    response = client.post(
        "/tasks",
        json={"title": "   "},
        headers=auth_headers(token),
    )
    assert response.status_code == 422


def test_update_task_rejects_blank_title(client):
    token = register_and_login(client, "titulo_vazio_update@example.com")

    create_response = client.post(
        "/tasks",
        json={"title": "Titulo valido"},
        headers=auth_headers(token),
    )
    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "   "},
        headers=auth_headers(token),
    )
    assert response.status_code == 422


def test_list_tasks_filters_by_status(client):
    token = register_and_login(client, "filtro_status@example.com")

    todo_response = client.post(
        "/tasks", json={"title": "A fazer"}, headers=auth_headers(token)
    )
    done_response = client.post(
        "/tasks", json={"title": "Feita"}, headers=auth_headers(token)
    )
    client.patch(
        f"/tasks/{done_response.json()['id']}",
        json={"status": "done"},
        headers=auth_headers(token),
    )

    response = client.get("/tasks?status=done", headers=auth_headers(token))
    data = response.json()

    assert response.status_code == 200
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == done_response.json()["id"]
    assert all(item["status"] == "done" for item in data["items"])
