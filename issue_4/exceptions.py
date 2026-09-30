class BaseItemRepositoryError(Exception):
    pass


class ItemNotFoundError(BaseItemRepositoryError):
    def __init__(self, item_id: str):
        super().__init__(f"item '{item_id}' not found")
        self.item_id = item_id


class AlreadyExistsError(BaseItemRepositoryError):
    def __init__(self, item_id: str):
        super().__init__(f"item '{item_id}' already exists")
        self.item_id = item_id


class VersionConflictError(BaseItemRepositoryError):
    def __init__(self, item_id: str):
        super().__init__(f"wrong version for '{item_id}'")
        self.item_id = item_id