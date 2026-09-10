from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class Location(BaseModel):
    """Location model"""
    latitude: float
    longitude: float
    bbox: Optional[List[float]] = None
    name: Optional[str] = None


class ImageryRequest(BaseModel):
    """Request for satellite imagery"""
    latitude: float
    longitude: float
    bbox: Optional[List[float]] = None
    date: str
    satellite: str = "sentinel-2"
    max_cloud_cover: Optional[float] = 20.0


class SatelliteImage(BaseModel):
    """Satellite image model"""
    image_id: str
    image_url: str
    date: str
    satellite: str
    bbox: List[float]
    metadata: dict = {}


class ImageryResponse(BaseModel):
    """Response for satellite imagery request"""
    image_id: str
    image_url: str
    date: str
    satellite: str
    bbox: List[float]
    metadata: dict = {}


class QuestionRequest(BaseModel):
    """Request for image question answering"""
    image_id: str
    question: str
    location: Optional[Location] = None


class AnalysisResponse(BaseModel):
    """Response for analysis requests"""
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    observations: List[str] = []
    limitations: List[str] = []
    regions: Optional[List[Any]] = None


class ChangedRegion(BaseModel):
    """Changed region model"""
    id: int
    bbox: List[float]
    area: float
    confidence: float = Field(ge=0.0, le=1.0)
    description: Optional[str] = None


class ComparisonRequest(BaseModel):
    """Request for image comparison"""
    bbox: List[float]
    date_before: str
    date_after: str


class ChangeAnalysisResponse(BaseModel):
    """Response for change analysis"""
    before_image: SatelliteImage
    after_image: SatelliteImage
    changed_regions: List[ChangedRegion]
    change_mask: Optional[str] = None
    summary: str


class ConstructionAnalysisResponse(BaseModel):
    """Response for construction analysis"""
    candidate_regions: List[ChangedRegion]
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: List[str] = []


class Report(BaseModel):
    """Report model"""
    location: Location
    date_before: str
    date_after: str
    imagery: str
    summary: str
    detected_changes: int
    potential_construction_regions: int
    key_regions: List[int]
    confidence: str  # "High", "Medium", "Low"
    limitations: List[str]


class ReportRequest(BaseModel):
    """Request for report generation"""
    location: Location
    date_before: str
    date_after: str
    include_change_analysis: bool = True


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    demo_mode: bool
    timestamp: datetime


class SuperResolutionRequest(BaseModel):
    """Request for SR processing of a server-side GeoTIFF."""
    input_path: Optional[str] = None
    reference_path: Optional[str] = None
    tile_size: Optional[int] = None
    overlap: Optional[int] = None
    bbox: Optional[List[float]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    date: Optional[str] = None
    max_cloud_cover: Optional[float] = 20.0


class SuperResolutionResponse(BaseModel):
    """Georeferenced SR result and optional objective metrics."""
    input_url: str
    output_url: str
    input_preview_url: str
    output_preview_url: str
    model: str
    scale: int
    input_width: int
    input_height: int
    output_width: int
    output_height: int
    input_resolution_m: float
    output_resolution_m: float
    processing_time_seconds: float
    metrics: Optional[dict] = None
    validation_message: Optional[str] = None