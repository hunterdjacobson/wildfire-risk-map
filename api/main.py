import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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

@app.on_event("startup")
async def startup_event():
    print("Wildfire Risk API started")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "wildfire-risk-api"}

# TODO: Include routers here later
# app.include_router(...)
