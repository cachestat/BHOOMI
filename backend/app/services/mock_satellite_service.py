from app.models.schemas import ImageryRequest, ImageryResponse
from typing import Dict, Any
import uuid


class MockSatelliteService:
    """Mock satellite service for demo mode"""
    
    def __init__(self):
        # Sample demo locations with mock imagery data
        self.demo_locations = {
            "new york": {
                "name": "New York City",
                "lat": 40.7128,
                "lng": -74.0060,
                "bbox": [-74.1, 40.6, -73.9, 40.8]
            },
            "london": {
                "name": "London",
                "lat": 51.5074,
                "lng": -0.1278,
                "bbox": [-0.2, 51.4, 0.0, 51.6]
            },
            "tokyo": {
                "name": "Tokyo",
                "lat": 35.6762,
                "lng": 139.6503,
                "bbox": [139.5, 35.5, 139.8, 35.8]
            },
            "delhi": {
                "name": "Delhi",
                "lat": 28.7041,
                "lng": 77.1025,
                "bbox": [76.9, 28.5, 77.3, 28.9]
            },
            "mumbai": {
                "name": "Mumbai",
                "lat": 19.0760,
                "lng": 72.8777,
                "bbox": [72.7, 18.9, 73.1, 19.2]
            }
        }
    
    async def search_imagery(self, request: ImageryRequest) -> Dict[str, Any]:
        """Search for available satellite imagery (mock)"""
        # Simulate search delay
        import asyncio
        await asyncio.sleep(0.5)
        
        # Return mock search results
        return {
            "total_results": 5,
            "results": [
                {
                    "image_id": str(uuid.uuid4()),
                    "date": request.date,
                    "satellite": request.satellite,
                    "cloud_cover": 5.2,
                    "resolution": 10.0,
                    "bbox": request.bbox or self._get_default_bbox(request.latitude, request.longitude)
                }
            ]
        }
    
    async def get_imagery(self, request: ImageryRequest) -> ImageryResponse:
        """Get satellite imagery data (mock)"""
        # Simulate retrieval delay
        import asyncio
        await asyncio.sleep(1.0)
        
        # Generate mock image URL (in production, this would be real satellite imagery)
        image_id = str(uuid.uuid4())
        bbox = request.bbox or self._get_default_bbox(request.latitude, request.longitude)
        
        return ImageryResponse(
            image_id=image_id,
            image_url=f"/api/demo/images/{image_id}",  # Mock URL
            date=request.date,
            satellite=request.satellite,
            bbox=bbox,
            metadata={
                "cloud_cover": 5.2,
                "resolution": 10.0,
                "processing_level": "L2A",
                "demo_mode": True
            }
        )
    
    def _get_default_bbox(self, lat: float, lng: float) -> list:
        """Generate default bounding box around coordinates"""
        return [lng - 0.01, lat - 0.01, lng + 0.01, lat + 0.01]