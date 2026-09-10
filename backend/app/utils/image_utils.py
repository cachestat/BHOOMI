from PIL import Image
import numpy as np
from typing import Tuple, Optional
import io


def resize_image(image: Image.Image, max_size: Tuple[int, int] = (1024, 1024)) -> Image.Image:
    """Resize image while maintaining aspect ratio"""
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return image


def convert_to_rgb(image: Image.Image) -> Image.Image:
    """Convert image to RGB format"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return image


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize image array to 0-1 range"""
    if image.max() > 1.0:
        image = image.astype(np.float32) / 255.0
    return image


def image_to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
    """Convert PIL Image to bytes"""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=format)
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


def bytes_to_image(image_bytes: bytes) -> Image.Image:
    """Convert bytes to PIL Image"""
    return Image.open(io.BytesIO(image_bytes))


def crop_image(image: Image.Image, bbox: Tuple[int, int, int, int]) -> Image.Image:
    """Crop image to bounding box"""
    return image.crop(bbox)


def calculate_bbox_from_coords(
    center_lat: float, 
    center_lng: float, 
    width_meters: float,
    height_meters: float
) -> Tuple[float, float, float, float]:
    """Calculate bounding box from center coordinates and dimensions in meters"""
    # Approximate conversion (should use proper projection in production)
    lat_offset = height_meters / 111111  # meters per degree latitude
    lng_offset = width_meters / (111111 * np.cos(np.radians(center_lat)))
    
    return (
        center_lng - lng_offset,
        center_lat - lat_offset,
        center_lng + lng_offset,
        center_lat + lat_offset
    )