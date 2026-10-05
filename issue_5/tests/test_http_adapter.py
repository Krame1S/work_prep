from fastapi.testclient import TestClient
from app import create_app
from service import ItemService
from repository import InMemoryItemRepository


def make_client():
    service = ItemService(InMemoryItemRepository())
    app = create_app(service)
    return TestClient(app)


def test_create_item_returns_201_and_location():
    client = make_client()
    response = client.post('/items', json={'id': '1', 'name': 'name'})

    assert response.status_code == 201
    assert response.headers['Location'] == '/items/1'
    assert response.json() == {'id': '1', 'name': 'name', 'version': 1}


def test_get_item_returns_200():
    client = make_client()
    client.post('/items', json={'id': '1', 'name': 'name'})
    response = client.get('/items/1')

    assert response.status_code == 200
    assert response.json() == {'id': '1', 'name': 'name', 'version': 1}


def test_get_unknown_item_returns_404():
    client = make_client()
    response = client.get('/items/missing')

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'item_not_found'


def test_create_duplicate_id_returns_409_and_state_unchanged():
    client = make_client()
    client.post('/items', json={'id': '1', 'name': 'first'})
    response = client.post('/items', json={'id': '1', 'name': 'second'})

    assert response.status_code == 409
    assert response.json()['error']['code'] == 'already_exists'

    get_response = client.get('/items/1')
    assert get_response.json()['name'] == 'first'


def test_replace_wrong_version_returns_409_and_state_unchanged():
    client = make_client()
    client.post('/items', json={'id': '1', 'name': 'first'})
    response = client.put('/items/1?expected_version=99', json={'name': 'second'})

    assert response.status_code == 409
    assert response.json()['error']['code'] == 'version_conflict'

    get_response = client.get('/items/1')
    assert get_response.json() == {'id': '1', 'name': 'first', 'version': 1}


def test_replace_unknown_item_returns_404():
    client = make_client()
    response = client.put('/items/missing?expected_version=1', json={'name': 'x'})

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'item_not_found'


def test_replace_returns_200_and_bumps_version():
    client = make_client()
    client.post('/items', json={'id': '1', 'name': 'first'})
    response = client.put('/items/1?expected_version=1', json={'name': 'second'})

    assert response.status_code == 200
    assert response.json() == {'id': '1', 'name': 'second', 'version': 2}


def test_list_items_returns_200():
    client = make_client()
    client.post('/items', json={'id': '1', 'name': 'a'})
    client.post('/items', json={'id': '2', 'name': 'b'})
    response = client.get('/items')

    assert response.status_code == 200
    assert response.json() == [
        {'id': '1', 'name': 'a', 'version': 1},
        {'id': '2', 'name': 'b', 'version': 1},
    ]


def test_delete_returns_204_with_empty_body():
    client = make_client()
    client.post('/items', json={'id': '1', 'name': 'a'})
    response = client.delete('/items/1')

    assert response.status_code == 204
    assert response.content == b''

    get_response = client.get('/items/1')
    assert get_response.status_code == 404


def test_delete_unknown_item_returns_404():
    client = make_client()
    response = client.delete('/items/missing')

    assert response.status_code == 404


def test_create_with_empty_name_returns_422_and_state_unchanged():
    client = make_client()
    response = client.post('/items', json={'id': '1', 'name': ''})

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'validation_error'

    list_response = client.get('/items')
    assert list_response.json() == []



def test_add_item_same_result_with_service_and_http():
    service = ItemService(InMemoryItemRepository())
    direct = service.add_item(item_id='1', name='name')

    other_service = ItemService(InMemoryItemRepository())
    client = TestClient(create_app(other_service))
    http_response = client.post('/items', json={'id': '1', 'name': 'name'})

    assert http_response.status_code == 201
    assert http_response.json() == {
        'id': direct.id,
        'name': direct.name,
        'version': direct.version,
    }


def test_create_missing_field_returns_consistent_validation_format():
    client = make_client()
    response = client.post('/items', json={'id': '1'})

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'validation_error'

    list_response = client.get('/items')
    assert list_response.json() == []


def test_replace_bad_expected_version_type_returns_consistent_validation_format():
    client = make_client()
    client.post('/items', json={'id': '1', 'name': 'first'})
    response = client.put('/items/1?expected_version=bad', json={'name': 'second'})

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'validation_error'

    get_response = client.get('/items/1')
    assert get_response.json() == {'id': '1', 'name': 'first', 'version': 1}


def test_unexpected_value_error_returns_generic_500():
    class BrokenService(ItemService):
        def get_item(self, item_id):
            raise ValueError('internal database detail')

    client = TestClient(
        create_app(BrokenService(InMemoryItemRepository())),
        raise_server_exceptions=False,
    )
    response = client.get('/items/1')

    assert response.status_code == 500
    assert response.json() == {
        'error': {'code': 'internal_error', 'message': 'Internal server error'}
    }
    assert 'internal database detail' not in response.text


def test_unexpected_runtime_error_returns_generic_500():
    class BrokenService(ItemService):
        def get_item(self, item_id):
            raise RuntimeError('boom')

    client = TestClient(
        create_app(BrokenService(InMemoryItemRepository())),
        raise_server_exceptions=False,
    )
    response = client.get('/items/1')

    assert response.status_code == 500
    assert response.json() == {
        'error': {'code': 'internal_error', 'message': 'Internal server error'}
    }


def test_create_with_unsupported_id_characters_returns_422_and_state_unchanged():
    client = make_client()
    response = client.post('/items', json={'id': 'a?b', 'name': 'x'})

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'validation_error'

    list_response = client.get('/items')
    assert list_response.json() == []


def test_create_with_non_ascii_id_returns_422_and_state_unchanged():
    client = make_client()
    response = client.post('/items', json={'id': 'Илья', 'name': 'x'})

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'validation_error'

    list_response = client.get('/items')
    assert list_response.json() == []


def test_create_with_slash_in_id_returns_422_and_state_unchanged():
    client = make_client()
    response = client.post('/items', json={'id': 'a/b', 'name': 'x'})

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'validation_error'

    list_response = client.get('/items')
    assert list_response.json() == []


def test_create_location_header_is_reachable():
    client = make_client()
    response = client.post('/items', json={'id': 'abc-123_ok', 'name': 'x'})

    assert response.status_code == 201

    follow = client.get(response.headers['Location'])
    assert follow.status_code == 200
    assert follow.json() == {'id': 'abc-123_ok', 'name': 'x', 'version': 1}
