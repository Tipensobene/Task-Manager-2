from fastapi import FastAPI


from task_routes import task_router
app = FastAPI(title="Task Manager 4.0")



app.include_router(task_router)


