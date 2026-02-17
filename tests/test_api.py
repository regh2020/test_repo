"""Tests for API endpoints."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_create_and_get_conference(client):
    resp = client.post(
        "/conferences",
        json={"name": "ICML 2026", "acronym": "ICML", "city": "Vienna", "country": "Austria"},
    )
    assert resp.status_code == 201
    conf = resp.json()
    assert conf["name"] == "ICML 2026"
    conf_id = conf["id"]

    resp = client.get(f"/conferences/{conf_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "ICML 2026"


def test_list_conferences(client):
    client.post("/conferences", json={"name": "Conf A"})
    client.post("/conferences", json={"name": "Conf B"})
    resp = client.get("/conferences")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_conferences_filter_by_name(client):
    client.post("/conferences", json={"name": "ICML 2026"})
    client.post("/conferences", json={"name": "NeurIPS 2026"})

    resp = client.get("/conferences", params={"name": "ICML"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "ICML 2026"


def test_update_conference(client):
    resp = client.post("/conferences", json={"name": "Test"})
    conf_id = resp.json()["id"]

    resp = client.patch(f"/conferences/{conf_id}", json={"name": "Updated", "city": "Berlin"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert resp.json()["city"] == "Berlin"


def test_delete_conference(client):
    resp = client.post("/conferences", json={"name": "To Delete"})
    conf_id = resp.json()["id"]

    resp = client.delete(f"/conferences/{conf_id}")
    assert resp.status_code == 204

    resp = client.get(f"/conferences/{conf_id}")
    assert resp.status_code == 404


def test_conference_not_found(client):
    resp = client.get("/conferences/nonexistent")
    assert resp.status_code == 404


def test_add_and_list_dates(client):
    resp = client.post("/conferences", json={"name": "Test"})
    conf_id = resp.json()["id"]

    resp = client.post(
        f"/conferences/{conf_id}/dates",
        json={"type": "submission_deadline", "date_time": "2026-06-15"},
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "submission_deadline"

    resp = client.get(f"/conferences/{conf_id}/dates")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_add_and_list_sources(client):
    resp = client.post("/conferences", json={"name": "Test"})
    conf_id = resp.json()["id"]

    resp = client.post(
        f"/conferences/{conf_id}/sources",
        json={"type": "website", "url": "https://example.com/conf"},
    )
    assert resp.status_code == 201
    assert resp.json()["url"] == "https://example.com/conf"

    resp = client.get(f"/conferences/{conf_id}/sources")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_refresh_endpoint(client):
    resp = client.post("/refresh", json={})
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_discover_endpoint(client):
    resp = client.post(
        "/discover",
        json={"keywords": ["machine learning"], "topics": ["AI"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert "candidates" in data
