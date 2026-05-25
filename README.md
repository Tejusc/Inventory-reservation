# Inventory Reservation System

A RESTful API for managing inventory and reservations, built with Python and FastAPI.

---

## Table of Contents

- [Phases](#phases)
- [Getting Started](#getting-started)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How to Run](#how-to-run)
- [Clean Run Process](#clean-run-process)
- [API Reference](#api-reference)
- [Demo Script](#demo-script)

---

## Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Complete | Project scaffold, Items CRUD, availability endpoint |
| 2 | 🔜 Pending | Reservations — create and query |
| 3 | 🔜 Pending | Reservation lifecycle — confirm, cancel, fulfill |
| 4 | 🔜 Pending | Filtering, pagination, expiry |

---

## Getting Started

**Prerequisites:** Python 3.9+

```bash
git clone https://github.com/Tejusc/Inventory-reservation.git
cd Inventory-reservation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.9+ |
| Framework | FastAPI 0.111 |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Testing | pytest + httpx TestClient |
| Storage | In-memory (DB-ready repository interface) |

---

## Project Structure

```
app/
  main.py                         # FastAPI app factory
  models/
    item.py                       # Item domain model + request/response schemas
  routes/
    health.py                     # GET /health
    items.py                      # Items CRUD routes
  services/
    item_service.py               # Item business logic
  repositories/
    item_repository.py            # ItemRepository ABC
    in_memory/
      item_repo.py                # InMemoryItemRepository
tests/
  conftest.py                     # Shared fixtures
  test_item_service.py            # Service-layer unit tests
  test_item_routes.py             # Route-layer integration tests
requirements.txt
README.md
```

**Architecture rule:** Routes call services. Services call repositories. No layer skips another.

---

## How to Run

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

API will be available at `http://127.0.0.1:8000`

Interactive docs: `http://127.0.0.1:8000/docs`

---

## Clean Run Process

```bash
# 1. Create a fresh virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run tests
pytest tests/ -v

# 4. Start the server
uvicorn app.main:app --reload
```

---

## API Reference

### Health

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/health` | Liveness check | `{"status": "ok"}` |

### Items

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/items` | Create a new item | 201 |
| GET | `/items` | List all items (paginated) | 200 |
| GET | `/items/{item_id}` | Get item by ID | 200 |
| PUT | `/items/{item_id}` | Update item fields | 200 |
| DELETE | `/items/{item_id}` | Delete an item | 204 |
| GET | `/items/{item_id}/availability` | Get stock availability | 200 |

#### Create Item — `POST /items`

**Request**
```json
{
  "name": "Widget",
  "sku": "WGT-001",
  "description": "A standard widget",
  "total_quantity": 100
}
```

**Response 201**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Widget",
  "sku": "WGT-001",
  "description": "A standard widget",
  "total_quantity": 100,
  "reserved_quantity": 0,
  "available_quantity": 100,
  "created_at": "2026-05-25T10:00:00Z",
  "updated_at": "2026-05-25T10:00:00Z"
}
```

#### Get Availability — `GET /items/{item_id}/availability`

**Response 200**
```json
{
  "item_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "total_quantity": 100,
  "reserved_quantity": 10,
  "available_quantity": 90
}
```

---

## Demo Script

```bash
BASE=http://127.0.0.1:8000

# Health check
curl $BASE/health

# Create an item
curl -s -X POST $BASE/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Widget","sku":"WGT-001","total_quantity":100}' | python3 -m json.tool

# List items
curl -s $BASE/items | python3 -m json.tool

# Get item by ID (replace <id> with the id from create response)
curl -s $BASE/items/<id> | python3 -m json.tool

# Check availability
curl -s $BASE/items/<id>/availability | python3 -m json.tool

# Update item
curl -s -X PUT $BASE/items/<id> \
  -H "Content-Type: application/json" \
  -d '{"total_quantity":200}' | python3 -m json.tool

# Delete item
curl -s -X DELETE $BASE/items/<id> -o /dev/null -w "%{http_code}\n"
```
