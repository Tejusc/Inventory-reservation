from __future__ import annotations

import pytest


@pytest.fixture
def item(client):
    resp = client.post(
        "/items", json={"name": "Widget", "sku": "WGT-001", "total_quantity": 50}
    )
    return resp.json()


def test_create_reservation_201(client, item):
    resp = client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 10, "requester_id": "user-1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["item_id"] == item["id"]
    assert body["quantity"] == 10
    assert body["status"] == "PENDING"
    assert body["requester_id"] == "user-1"
    assert "id" in body
    assert "created_at" in body


def test_create_reservation_reduces_availability(client, item):
    client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 10, "requester_id": "user-1"},
    )
    avail = client.get(f"/items/{item['id']}/availability").json()
    assert avail["reserved_quantity"] == 10
    assert avail["available_quantity"] == 40


def test_create_reservation_insufficient_quantity_409(client, item):
    resp = client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 999, "requester_id": "user-1"},
    )
    assert resp.status_code == 409


def test_create_reservation_item_not_found_404(client):
    resp = client.post(
        "/reservations",
        json={
            "item_id": "00000000-0000-0000-0000-000000000000",
            "quantity": 1,
            "requester_id": "user-1",
        },
    )
    assert resp.status_code == 404


def test_create_reservation_invalid_quantity_422(client, item):
    resp = client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 0, "requester_id": "user-1"},
    )
    assert resp.status_code == 422


def test_get_reservation_200(client, item):
    created = client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 5, "requester_id": "user-1"},
    ).json()
    resp = client.get(f"/reservations/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_reservation_not_found_404(client):
    resp = client.get("/reservations/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_list_reservations_empty_200(client):
    resp = client.get("/reservations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_reservations_returns_created(client, item):
    client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 1, "requester_id": "user-1"},
    )
    client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 1, "requester_id": "user-2"},
    )
    resp = client.get("/reservations")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_reservations_filter_by_item_id(client, item):
    other = client.post(
        "/items", json={"name": "Other", "sku": "OTH-001", "total_quantity": 10}
    ).json()
    client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 1, "requester_id": "u1"},
    )
    client.post(
        "/reservations",
        json={"item_id": other["id"], "quantity": 1, "requester_id": "u2"},
    )
    resp = client.get(f"/reservations?item_id={item['id']}")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["item_id"] == item["id"]


def test_list_reservations_filter_by_status(client, item):
    client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 1, "requester_id": "u1"},
    )
    resp = client.get("/reservations?status=PENDING")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/reservations?status=CONFIRMED")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_list_reservations_filter_by_requester_id(client, item):
    client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 1, "requester_id": "alice"},
    )
    client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 1, "requester_id": "bob"},
    )
    resp = client.get("/reservations?requester_id=alice")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["requester_id"] == "alice"


def test_list_reservations_pagination(client, item):
    for i in range(5):
        client.post(
            "/reservations",
            json={"item_id": item["id"], "quantity": 1, "requester_id": f"u{i}"},
        )
    resp = client.get("/reservations?skip=2&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
