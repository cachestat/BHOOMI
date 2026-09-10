from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import imagery, srm
import uvicorn

app = FastAPI(
    title="Satellite Super-Resolution Mapping API",
    description="Sentinel-2 retrieval and geospatial super-resolution prototype",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(imagery.router, prefix="/api/imagery", tags=["imagery"])
app.include_router(srm.router, prefix="/api/srm", tags=["super-resolution"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    from app.models.schemas import HealthResponse
    
    return HealthResponse(
        status="healthy",
        demo_mode=settings.demo_mode,
        timestamp=datetime.utcnow()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SatQuery AI API",
        "version": "1.0.0",
        "demo_mode": settings.demo_mode,
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=True
    )