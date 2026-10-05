from fastapi import FastAPI, Response
from errors import register_error_handlers
from schemas import ItemIn, ItemOut, ItemUpdate
from service import ItemService



def create_app(service: ItemService):
    app = FastAPI()

    register_error_handlers(app)

    @app.post('/items', status_code=201, response_model=ItemOut)
    def create_item(item: ItemIn, response: Response):
        created = service.add_item(item_id=item.id, name=item.name)
        response.headers['Location'] = f'/items/{created.id}'
        return created

    @app.get('/items/{item_id}', status_code=200, response_model=ItemOut)
    def get_item(item_id: str):
        return service.get_item(item_id)

    @app.get('/items', status_code=200, response_model=list[ItemOut])
    def list_items():
        return service.list_items()

    @app.put('/items/{item_id}', status_code=200, response_model=ItemOut)
    def replace_item(item_id: str, item: ItemUpdate, expected_version: int):
        return service.replace_item(item_id, item.name, expected_version)

    @app.delete('/items/{item_id}', status_code=204)
    def delete_item(item_id: str):
        service.delete_item(item_id)


    return app

