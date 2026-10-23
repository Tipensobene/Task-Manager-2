from fastapi import FastAPI


from ai_routes import ai_router
from task_routes import task_router
app = FastAPI(title="Task Manager 4.0")



app.include_router(task_router)

app.include_router(ai_router)


