from app.models.schemas import ComparisonRequest, ChangeAnalysisResponse, SatelliteImage, ChangedRegion
from typing import List
import uuid


class MockChangeDetectionService:
    """Mock change detection service for demo mode"""
    
    async def detect_changes(
        self, 
        bbox: List[float], 
        date_before: str, 
        date_after: str
    ) -> ChangeAnalysisResponse:
        """Detect changes between two satellite images (mock)"""
        import asyncio
        await asyncio.sleep(1.5)  # Simulate processing time
        
        # Generate mock changed regions
        changed_regions = self._generate_mock_regions(bbox)
        
        # Create mock satellite images
        before_image = SatelliteImage(
            image_id=str(uuid.uuid4()),
            image_url=f"/api/demo/images/before_{date_before}",
            date=date_before,
            satellite="Sentinel-2",
            bbox=bbox,
            metadata={"cloud_cover": 5.0, "resolution": 10.0}
        )
        
        after_image = SatelliteImage(
            image_id=str(uuid.uuid4()),
            image_url=f"/api/demo/images/after_{date_after}",
            date=date_after,
            satellite="Sentinel-2",
            bbox=bbox,
            metadata={"cloud_cover": 3.0, "resolution": 10.0}
        )
        
        return ChangeAnalysisResponse(
            before_image=before_image,
            after_image=after_image,
            changed_regions=changed_regions,
            change_mask="/api/demo/masks/change_mask.png",
            summary=f"Detected {len(changed_regions)} regions with significant changes between {date_before} and {date_after}. Changes are primarily concentrated in the northern and eastern areas of the selected region."
        )
    
    def _generate_mock_regions(self, bbox: List[float]) -> List[ChangedRegion]:
        """Generate mock changed regions"""
        regions = []
        base_lat = (bbox[1] + bbox[3]) / 2
        base_lng = (bbox[0] + bbox[2]) / 2
        
        # Generate 8-12 mock changed regions
        num_regions = 8 + (hash(str(bbox)) % 5)
        
        for i in range(num_regions):
            # Generate region around the center with some variation
            offset_lat = (i % 3 - 1) * 0.005
            offset_lng = (i // 3 - 1) * 0.005
            
            region_bbox = [
                base_lng + offset_lng - 0.002,
                base_lat + offset_lat - 0.002,
                base_lng + offset_lng + 0.002,
                base_lat + offset_lat + 0.002
            ]
            
            regions.append(ChangedRegion(
                id=i + 1,
                bbox=region_bbox,
                area=1000 + (i * 200),  # Mock area in square meters
                confidence=0.7 + (i * 0.02),  # Varying confidence
                description=f"Region {i+1} shows visual changes consistent with development activity"
            ))
        
        return regions