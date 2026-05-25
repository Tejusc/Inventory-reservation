import pytest

from app.services.item_service import ItemService, ItemNotFoundError, DuplicateSKUError
from app.models.item import CreateItemRequest, UpdateItemRequest
from app.repositories.in_memory.item_repo import InMemoryItemRepository


@pytest.fixture
def service() -> ItemService:
    return ItemService(repository=InMemoryItemRepository())


def test_create_item_returns_item_with_id(service):
    req = CreateItemRequest(name="Widget", sku="WGT-001", total_quantity=100)
    item = service.create_item(req)

    assert item.id is not None
    assert item.name == "Widget"
    assert item.sku == "WGT-001"
    assert item.total_quantity == 100
    assert item.reserved_quantity == 0
    assert item.available_quantity == 100
    assert item.created_at is not None
    assert item.updated_at is not None


def test_create_item_duplicate_sku_raises(service):
    req = CreateItemRequest(name="Widget", sku="WGT-001", total_quantity=10)
    service.create_item(req)

    with pytest.raises(DuplicateSKUError):
        service.create_item(CreateItemRequest(name="Other", sku="WGT-001", total_quantity=5))


def test_get_item_returns_existing(service):
    req = CreateItemRequest(name="Gadget", sku="GDG-001", total_quantity=50)
    created = service.create_item(req)

    fetched = service.get_item(created.id)
    assert fetched.id == created.id
    assert fetched.name == "Gadget"


def test_get_item_not_found_raises(service):
    from uuid import uuid4
    with pytest.raises(ItemNotFoundError):
        service.get_item(uuid4())


def test_list_items_empty(service):
    assert service.list_items() == []


def test_list_items_returns_all(service):
    service.create_item(CreateItemRequest(name="A", sku="A-001", total_quantity=1))
    service.create_item(CreateItemRequest(name="B", sku="B-001", total_quantity=2))

    items = service.list_items()
    assert len(items) == 2


def test_list_items_pagination(service):
    for i in range(5):
        service.create_item(CreateItemRequest(name=f"Item{i}", sku=f"SKU-{i:03}", total_quantity=i + 1))

    page = service.list_items(skip=2, limit=2)
    assert len(page) == 2


def test_update_item_changes_fields(service):
    created = service.create_item(CreateItemRequest(name="Old", sku="OLD-001", total_quantity=10))
    updated = service.update_item(created.id, UpdateItemRequest(name="New", total_quantity=20))

    assert updated.name == "New"
    assert updated.total_quantity == 20
    assert updated.sku == "OLD-001"


def test_update_item_not_found_raises(service):
    from uuid import uuid4
    with pytest.raises(ItemNotFoundError):
        service.update_item(uuid4(), UpdateItemRequest(name="X"))


def test_delete_item_removes_it(service):
    created = service.create_item(CreateItemRequest(name="Temp", sku="TMP-001", total_quantity=5))
    service.delete_item(created.id)

    with pytest.raises(ItemNotFoundError):
        service.get_item(created.id)


def test_delete_item_not_found_raises(service):
    from uuid import uuid4
    with pytest.raises(ItemNotFoundError):
        service.delete_item(uuid4())


def test_get_availability(service):
    created = service.create_item(CreateItemRequest(name="Stock", sku="STK-001", total_quantity=30))
    availability = service.get_availability(created.id)

    assert availability.item_id == created.id
    assert availability.total_quantity == 30
    assert availability.reserved_quantity == 0
    assert availability.available_quantity == 30
