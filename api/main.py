import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers.fires import router as fires_router
from routers.risk import router as risk_router
from services.scheduler import start_scheduler

# Load .env file
load_dotenv()

app = FastAPI(title="Wildfire Risk API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(fires_router)
app.include_router(risk_router)

@app.on_event("startup")
async def startup_event():
    print("Wildfire Risk API started")
    api_key = os.getenv("FIRMS_API_KEY")
    if api_key:
        app.state.scheduler = start_scheduler(api_key)
        print("Background scheduler started")
    else:
        print("FIRMS_API_KEY not found, scheduler NOT started")

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
        print("Background scheduler shutdown")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "wildfire-risk-api"}
