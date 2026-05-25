import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_item_201(client):
    resp = client.post("/items", json={"name": "Widget", "sku": "WGT-001", "total_quantity": 100})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Widget"
    assert body["sku"] == "WGT-001"
    assert body["total_quantity"] == 100
    assert body["reserved_quantity"] == 0
    assert body["available_quantity"] == 100
    assert "id" in body
    assert "created_at" in body


def test_create_item_duplicate_sku_409(client):
    client.post("/items", json={"name": "Widget", "sku": "WGT-001", "total_quantity": 10})
    resp = client.post("/items", json={"name": "Other", "sku": "WGT-001", "total_quantity": 5})
    assert resp.status_code == 409


def test_create_item_invalid_quantity_422(client):
    resp = client.post("/items", json={"name": "Bad", "sku": "BAD-001", "total_quantity": -1})
    assert resp.status_code == 422


def test_get_item_200(client):
    created = client.post("/items", json={"name": "Gadget", "sku": "GDG-001", "total_quantity": 50}).json()
    resp = client.get(f"/items/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_item_not_found_404(client):
    resp = client.get("/items/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_list_items_empty_200(client):
    resp = client.get("/items")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_items_returns_created(client):
    client.post("/items", json={"name": "A", "sku": "A-001", "total_quantity": 1})
    client.post("/items", json={"name": "B", "sku": "B-001", "total_quantity": 2})
    resp = client.get("/items")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_items_pagination(client):
    for i in range(5):
        client.post("/items", json={"name": f"Item{i}", "sku": f"ITM-{i:03}", "total_quantity": i + 1})
    resp = client.get("/items?skip=2&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_item_200(client):
    created = client.post("/items", json={"name": "Old", "sku": "OLD-001", "total_quantity": 10}).json()
    resp = client.put(f"/items/{created['id']}", json={"name": "New", "total_quantity": 20})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "New"
    assert body["total_quantity"] == 20


def test_update_item_not_found_404(client):
    resp = client.put("/items/00000000-0000-0000-0000-000000000000", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_item_204(client):
    created = client.post("/items", json={"name": "Temp", "sku": "TMP-001", "total_quantity": 5}).json()
    resp = client.delete(f"/items/{created['id']}")
    assert resp.status_code == 204


def test_delete_item_not_found_404(client):
    resp = client.delete("/items/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_get_availability_200(client):
    created = client.post("/items", json={"name": "Stock", "sku": "STK-001", "total_quantity": 30}).json()
    resp = client.get(f"/items/{created['id']}/availability")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_quantity"] == 30
    assert body["available_quantity"] == 30
    assert body["reserved_quantity"] == 0
