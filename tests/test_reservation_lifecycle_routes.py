from __future__ import annotations

import pytest


@pytest.fixture
def item(client):
    return client.post(
        "/items", json={"name": "Widget", "sku": "WGT-001", "total_quantity": 50}
    ).json()


@pytest.fixture
def pending(client, item):
    return client.post(
        "/reservations",
        json={"item_id": item["id"], "quantity": 10, "requester_id": "user-1"},
    ).json()


@pytest.fixture
def confirmed(client, pending):
    return client.post(f"/reservations/{pending['id']}/confirm").json()


# ── confirm ────────────────────────────────────────────────────────────────────

def test_confirm_200(client, pending):
    resp = client.post(f"/reservations/{pending['id']}/confirm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMED"


def test_confirm_not_found_404(client):
    resp = client.post("/reservations/00000000-0000-0000-0000-000000000000/confirm")
    assert resp.status_code == 404


def test_confirm_invalid_transition_409(client, pending):
    client.post(f"/reservations/{pending['id']}/confirm")
    resp = client.post(f"/reservations/{pending['id']}/confirm")
    assert resp.status_code == 409


# ── cancel ─────────────────────────────────────────────────────────────────────

def test_cancel_pending_200(client, pending):
    resp = client.post(f"/reservations/{pending['id']}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


def test_cancel_confirmed_200(client, confirmed):
    resp = client.post(f"/reservations/{confirmed['id']}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


def test_cancel_restores_availability(client, item, pending):
    client.post(f"/reservations/{pending['id']}/cancel")
    avail = client.get(f"/items/{item['id']}/availability").json()
    assert avail["reserved_quantity"] == 0
    assert avail["available_quantity"] == 50


def test_cancel_not_found_404(client):
    resp = client.post("/reservations/00000000-0000-0000-0000-000000000000/cancel")
    assert resp.status_code == 404


def test_cancel_invalid_transition_409(client, pending):
    client.post(f"/reservations/{pending['id']}/cancel")
    resp = client.post(f"/reservations/{pending['id']}/cancel")
    assert resp.status_code == 409


# ── fulfill ────────────────────────────────────────────────────────────────────

def test_fulfill_confirmed_200(client, confirmed):
    resp = client.post(f"/reservations/{confirmed['id']}/fulfill")
    assert resp.status_code == 200
    assert resp.json()["status"] == "FULFILLED"


def test_fulfill_updates_availability_and_total(client, item, confirmed):
    client.post(f"/reservations/{confirmed['id']}/fulfill")
    avail = client.get(f"/items/{item['id']}/availability").json()
    assert avail["reserved_quantity"] == 0
    assert avail["total_quantity"] == 40
    assert avail["available_quantity"] == 40


def test_fulfill_pending_409(client, pending):
    resp = client.post(f"/reservations/{pending['id']}/fulfill")
    assert resp.status_code == 409


def test_fulfill_not_found_404(client):
    resp = client.post("/reservations/00000000-0000-0000-0000-000000000000/fulfill")
    assert resp.status_code == 404


def test_fulfill_invalid_transition_409(client, confirmed):
    client.post(f"/reservations/{confirmed['id']}/fulfill")
    resp = client.post(f"/reservations/{confirmed['id']}/fulfill")
    assert resp.status_code == 409
