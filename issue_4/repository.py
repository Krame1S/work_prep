from dataclasses import dataclass
from typing import Protocol
from exceptions import AlreadyExistsError, ItemNotFoundError, VersionConflictError

@dataclass(frozen=True, slots=True)
class Item:
    id: str
    name: str
    version: int = 1

class ItemRepository(Protocol):
    def add(self, item: Item) -> None: ...
    def get(self, item_id: str) -> Item: ...
    def list(self) -> list[Item]: ...
    def replace(self, item_id: str, name: str, expected_version: int) -> Item: ...
    def delete(self, item_id: str) -> None: ...


class InMemoryItemRepository:
    def __init__(self):
        self.items: dict[str, Item] = {}


    def add(self, item: Item) -> None:
        if item.id in self.items:
            raise AlreadyExistsError(item.id)
        self.items[item.id] = item


    def get(self, item_id: str) -> Item:
        try:
            return self.items[item_id]
        except KeyError:
            raise ItemNotFoundError(item_id)


    def list(self) -> list[Item]:
        return list(self.items.values())


    def replace(self, item_id: str, name: str, expected_version: int) -> Item:
        try:
            to_replace = self.items[item_id]
        except KeyError:
            raise ItemNotFoundError(item_id)
        if to_replace.version != expected_version:
            raise VersionConflictError(item_id)
        new = Item(item_id, name, to_replace.version + 1)
        self.items[item_id] = new
        return new


    def delete(self, item_id: str) -> None:
        try:
            del self.items[item_id]
        except KeyError:
            raise ItemNotFoundError(item_id)