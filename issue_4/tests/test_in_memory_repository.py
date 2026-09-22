import pytest
from repository import InMemoryItemRepository
from service import ItemService
from exceptions import AlreadyExistsError, ItemNotFoundError, VersionConflictError

@pytest.fixture
def service():
    repository = InMemoryItemRepository()
    return ItemService(repository)


def test_get_item(service):
    service.add_item('1', 'item')
    got = service.get_item('1')
    assert got.id == '1'
    assert got.name == 'item'
    assert got.version == 1


def test_add_item(service):
    item = service.add_item('1', 'item')
    assert item.id == '1'
    assert item.name == 'item'
    assert item.version == 1

    added = service.get_item('1')
    assert added == item


def test_list_items(service):
    item1 = service.add_item('1', 'item1')
    item2 = service.add_item('2', 'item2')
    item3 = service.add_item('3', 'item3')

    added_items = service.list_items()

    assert added_items == [item1, item2, item3]


def test_replace_item(service):
    item = service.add_item('1', 'item1')

    replaced = service.replace_item('1', 'new name', item.version)

    assert replaced.id == '1'
    assert replaced.name == 'new name'
    assert replaced.version == item.version + 1

    added = service.get_item('1')
    assert added == replaced


def test_delete_item(service):
    item = service.add_item('1', 'item1')
    service.delete_item(item.id)

    assert item not in service.list_items()


def test_duplicate_add(service):
    item = service.add_item('1', 'item1')

    with pytest.raises(AlreadyExistsError):
        service.add_item('1', 'item1')

    unchanged = service.get_item('1')
    assert unchanged == item


def test_unknown_id_get(service):
    with pytest.raises(ItemNotFoundError):
        service.get_item('123')


def test_unknown_id_replace(service):
    with pytest.raises(ItemNotFoundError):
        service.replace_item('123', 'name', 1)


def test_unknown_id_delete(service):
    with pytest.raises(ItemNotFoundError):
        service.delete_item('123')


def test_version_conflict(service):
    item = service.add_item('1', 'item1')

    with pytest.raises(VersionConflictError):
        service.replace_item('1', 'item2', 2) 

    unchanged = service.get_item('1')
    assert unchanged == item


class FakeItemRepository:
    def __init__(self):
        self.added_items = []

    def add(self, item):
        self.added_items.append(item)

    def get(self, item_id):
        for item in self.added_items:
            if item.id == item_id:
                return item
        raise ItemNotFoundError(item_id)

    def list(self):
        return list(self.added_items)

    def replace(self, item_id, name, expected_version):
        raise NotImplementedError

    def delete(self, item_id):
        raise NotImplementedError


def test_independent_double():
    repository = FakeItemRepository()
    service = ItemService(repository)

    item = service.add_item('1', 'item')
    got = service.get_item('1')

    assert item == got 
