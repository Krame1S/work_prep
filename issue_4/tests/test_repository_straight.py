import pytest
from repository import Item, InMemoryItemRepository
from exceptions import ItemNotFoundError


def test_item_with_empty_id_raises():
    with pytest.raises(ValueError):
        Item('', 'name')


def test_item_with_empty_name_raises():
    with pytest.raises(ValueError):
        Item('1', '')


def test_add_rejects_empty_id_and_leaves_repository_empty():
    repo = InMemoryItemRepository()

    with pytest.raises(ValueError):
        repo.add(Item('', 'name'))

    assert repo.list() == []


def test_replace_rejects_empty_name_and_state_unchanged():
    repo = InMemoryItemRepository()
    repo.add(Item('1', 'first'))

    with pytest.raises(ValueError):
        repo.replace('1', '', 1)

    unchanged = repo.get('1')
    assert unchanged.name == 'first'
    assert unchanged.version == 1