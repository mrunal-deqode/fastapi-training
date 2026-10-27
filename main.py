from fastapi import FastAPI
from routers import applications, jobs

app = FastAPI(title="Recruitment & Hiring")

app.include_router(applications.router)
app.include_router(jobs.router)

@app.get("/")
def read_root():
    return {"message": "hello"}