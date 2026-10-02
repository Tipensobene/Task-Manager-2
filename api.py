from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse

from storage import StorageError

from task_routes import task_router
app = FastAPI(title="Task Manager3.0")


@app.exception_handler(StorageError)
def handle_storage_error(
        _request: Request,
        error: StorageError
):
    return JSONResponse(
        status_code=500,
        content={"detail": str(error)}
    )

app.include_router(task_router)


