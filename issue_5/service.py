import re

from repository import Item, ItemRepository
from exceptions import InvalidInputError

ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')


class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository

    def add_item(self, item_id: str, name: str) -> Item:
        if not item_id or not name:
            raise InvalidInputError('id and name must not be empty')
        if not ID_PATTERN.fullmatch(item_id):
            raise InvalidInputError('id contains unsupported characters')
        new = Item(item_id, name)
        self.repository.add(new)
        return new

    def get_item(self, item_id: str) -> Item:
        if not item_id:
            raise InvalidInputError('id must not be empty')
        return self.repository.get(item_id)

    def list_items(self) -> list[Item]:
        return self.repository.list()

    def replace_item(self, item_id: str, name: str, expected_version: int) -> Item:
        if not item_id or not name:
            raise InvalidInputError('id and name must not be empty')
        return self.repository.replace(item_id, name, expected_version)

    def delete_item(self, item_id: str) -> None:
        if not item_id:
            raise InvalidInputError('item_id must not be empty')
        self.repository.delete(item_id)