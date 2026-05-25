# Task List

Checked off as each item is completed. Updated after every phase.

---

## Phase 1 — Project Scaffold + Items CRUD ✅

- [x] Initialize git repo and connect to remote
- [x] Create project directory structure
- [x] Write `requirements.txt`
- [x] Write tests for Item service (TDD — before implementation)
- [x] Write tests for Item routes (TDD — before implementation)
- [x] Implement `Item` domain model and Pydantic schemas
- [x] Implement `ItemRepository` ABC
- [x] Implement `InMemoryItemRepository`
- [x] Implement `ItemService` (create, get, list, update, delete, availability)
- [x] Implement Item routes (`POST`, `GET`, `PUT`, `DELETE`, `GET /availability`)
- [x] Implement `GET /health` endpoint
- [x] Run tests — 26/26 passing
- [x] Write README with all Phase 1 endpoints
- [x] Add architecture diagrams to README
- [x] Push `phase-1` branch and open PR

---

## Phase 2 — Reservations (Create + Query) ✅

- [x] Write tests for Reservation service (TDD)
- [x] Write tests for Reservation routes (TDD)
- [x] Implement `ReservationStatus` enum
- [x] Implement `Reservation` domain model and Pydantic schemas
- [x] Implement `ReservationRepository` ABC
- [x] Implement `InMemoryReservationRepository`
- [x] Implement `ReservationService` (create, get, list with filters)
- [x] Implement Reservation routes (`POST /reservations`, `GET /reservations`, `GET /reservations/{id}`)
- [x] Run tests — 53/53 passing
- [x] Update README with Phase 2 endpoints
- [ ] Push `phase-2` branch and open PR ← awaiting your approval

---

## Phase 3 — Reservation Lifecycle 🔜

- [ ] Write tests for lifecycle transitions (TDD)
- [ ] Implement `POST /reservations/{id}/confirm`
- [ ] Implement `POST /reservations/{id}/cancel`
- [ ] Implement `POST /reservations/{id}/fulfill`
- [ ] Status transition guard (invalid transitions raise errors)
- [ ] Concurrency lock on `reserved_quantity` (threading.Lock in service)
- [ ] `reserved_quantity` on Item decremented on cancel/fulfill
- [ ] Run tests — all passing
- [ ] Update README with Phase 3 endpoints
- [ ] Push `phase-3` branch and open PR

---

## Phase 4 — Filtering, Pagination, Expiry 🔜

- [ ] Write tests for filters and expiry (TDD)
- [ ] Filter reservations by `status`, `item_id`, `requester_id`
- [ ] Pagination (`skip` / `limit`) on all list endpoints
- [ ] Expiry: `expires_at` field honoured — expired reservations auto-released
- [ ] Run tests — all passing
- [ ] Update README with Phase 4 query params
- [ ] Push `phase-4` branch and open PR
