"""FastAPI main application."""
from fastapi import FastAPI
from .database import init_db
from .api.routes import router

app = FastAPI(
    title="Dump Truck Contract Finder API",
    description="API for finding and managing dump truck contract awards",
    version="1.0.0"
)

# Include routers
app.include_router(router, prefix="", tags=["api"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_db()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Dump Truck Contract Finder API",
        "version": "1.0.0",
        "docs": "/docs"
    }

