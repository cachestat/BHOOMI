from fastapi import APIRouter, HTTPException
from app.models.schemas import ImageryRequest, ImageryResponse
from app.services.copernicus_service import CopernicusService

router = APIRouter()

satellite_service = CopernicusService()


@router.get("")
async def get_imagery():
    """Get available imagery information"""
    return {
        "message": "Copernicus satellite imagery service",
        "service": "copernicus"
    }


@router.post("/search")
async def search_imagery(request: ImageryRequest):
    """Search for satellite imagery"""
    try:
        result = await satellite_service.search_imagery(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def get_imagery_data(request: ImageryRequest):
    """Get satellite imagery data"""
    try:
        result = await satellite_service.get_imagery(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))