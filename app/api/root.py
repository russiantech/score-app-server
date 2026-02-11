# app/api/root.py
from fastapi import APIRouter
from app.utils.responses import api_response
from datetime import datetime

root_router = APIRouter(tags=["Root"], prefix="")

@root_router.get("/")
async def root():
    return api_response(
        success=True,
        message="Welcome to Dunistech Academy API ",
        data={
            "version": "0.2.0", "docs": "/docs",
            "team-lead": "Chris James"
            }
    )

@root_router.get("/health")
async def health():
    return api_response(
        success=True,
        message="App Running",
        data={"status": "healthy", "timestamp": datetime.now().isoformat() + "Z"}
    )
