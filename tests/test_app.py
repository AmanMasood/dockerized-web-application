import os

import pytest

os.environ["CREATE_APP_ON_IMPORT"] = "0"
from app.main import create_app  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("APP_ENV", "test")
    return create_app().test_client()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok"
    assert body["database"] is True
    assert body["environment"] == "test"


def test_task_lifecycle(client):
    assert client.get("/api/tasks").get_json() == []

    res = client.post("/api/tasks", json={"title": "Write Dockerfile"})
    assert res.status_code == 201
    task = res.get_json()
    assert task["title"] == "Write Dockerfile" and task["done"] is False

    res = client.patch(f"/api/tasks/{task['id']}", json={"done": True})
    assert res.get_json()["done"] is True

    assert client.delete(f"/api/tasks/{task['id']}").status_code == 204
    assert client.get("/api/tasks").get_json() == []


def test_validation_and_404(client):
    assert client.post("/api/tasks", json={}).status_code == 400
    assert client.patch("/api/tasks/999", json={"done": True}).status_code == 404
    assert client.delete("/api/tasks/999").status_code == 404


def test_data_persists_across_app_instances(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "persist.db"))
    create_app().test_client().post("/api/tasks", json={"title": "survives restart"})
    tasks = create_app().test_client().get("/api/tasks").get_json()
    assert [t["title"] for t in tasks] == ["survives restart"]
