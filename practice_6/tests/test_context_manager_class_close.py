import pytest
from context_manager_class_close import ManagedResource


class FakeResource:
    def __init__(self):
        self.exit_count = 0

    def close(self):
        self.exit_count += 1
        print('closed resource')

    
def test_exit_count_0_on_creation_inside_block_but_1_on_exit():
    resource = FakeResource()
    cm = ManagedResource(resource)

    assert resource.exit_count == 0  # после создания
    with cm as current:
        assert resource.exit_count == 0  # внутри блока
    assert resource.exit_count == 1  # после выхлда


def test_resource_identity():
    resource = FakeResource()

    with ManagedResource(resource) as current:
        assert current is resource


def test_exception_rises():
    resource = FakeResource()

    with pytest.raises(ValueError):
        with ManagedResource(resource) as current:
            raise ValueError

    assert resource.exit_count == 1
