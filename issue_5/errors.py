from fastapi import FastAPI
from fastapi.responses import JSONResponse
from exceptions import AlreadyExistsError, ItemNotFoundError, VersionConflictError


def register_error_handlers(app: FastAPI):
    app.add_exception_handler(ItemNotFoundError, handle_not_found)
    app.add_exception_handler(AlreadyExistsError, handle_already_exists)
    app.add_exception_handler(VersionConflictError, handle_version_conflict)
    app.add_exception_handler(ValueError, handle_validation)
    app.add_exception_handler(Exception, handle_unexpected)


def handle_not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={'error': {'code': 'item_not_found', 'message': str(exc)}},
    )


def handle_already_exists(request, exc):
    return JSONResponse(
        status_code=409,
        content={'error': {'code': 'already_exists', 'message': str(exc)}},
    )


def handle_version_conflict(request, exc):
    return JSONResponse(
        status_code=409,
        content={'error': {'code': 'version_conflict', 'message': str(exc)}},
    )


def handle_validation(request, exc):
    return JSONResponse(
        status_code=422,
        content={'error': {'code': 'validation_error', 'message': str(exc)}},
    )


def handle_unexpected(request, exc):
    return JSONResponse(
        status_code=500,
        content={'error': {'code': 'internal_error', 'message': 'Internal server error'}},
    )