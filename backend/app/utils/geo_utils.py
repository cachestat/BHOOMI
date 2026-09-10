import math
from typing import Tuple, List


def haversine_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """Calculate Haversine distance between two points in kilometers"""
    R = 6371  # Earth radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def bbox_to_center(bbox: List[float]) -> Tuple[float, float]:
    """Calculate center point of bounding box"""
    min_lng, min_lat, max_lng, max_lat = bbox
    center_lat = (min_lat + max_lat) / 2
    center_lng = (min_lng + max_lng) / 2
    return center_lat, center_lng


def bbox_to_area(bbox: List[float]) -> float:
    """Calculate approximate area of bounding box in square kilometers"""
    min_lng, min_lat, max_lng, max_lat = bbox
    
    # Calculate width and height in degrees
    width_deg = max_lng - min_lng
    height_deg = max_lat - min_lat
    
    # Convert to approximate kilometers (rough approximation)
    center_lat = (min_lat + max_lat) / 2
    width_km = width_deg * 111.32 * math.cos(math.radians(center_lat))
    height_km = height_deg * 110.574
    
    return width_km * height_km


def expand_bbox(
    bbox: List[float], 
    factor: float = 0.1
) -> List[float]:
    """Expand bounding box by a factor"""
    min_lng, min_lat, max_lng, max_lat = bbox
    
    width = max_lng - min_lng
    height = max_lat - min_lat
    
    expansion_width = width * factor
    expansion_height = height * factor
    
    return [
        min_lng - expansion_width,
        min_lat - expansion_height,
        max_lng + expansion_width,
        max_lat + expansion_height
    ]


def validate_bbox(bbox: List[float]) -> bool:
    """Validate bounding box format"""
    if len(bbox) != 4:
        return False
    
    min_lng, min_lat, max_lng, max_lat = bbox
    
    # Check longitude range
    if not (-180 <= min_lng <= 180) or not (-180 <= max_lng <= 180):
        return False
    
    # Check latitude range
    if not (-90 <= min_lat <= 90) or not (-90 <= max_lat <= 90):
        return False
    
    # Check that min < max
    if min_lng >= max_lng or min_lat >= max_lat:
        return False
    
    return True


def format_coordinates(lat: float, lng: float, precision: int = 6) -> str:
    """Format coordinates as string"""
    return f"{lat:.{precision}f}, {lng:.{precision}f}"