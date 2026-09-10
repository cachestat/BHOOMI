from pathlib import Path

import numpy as np
import rasterio
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import SuperResolutionRequest
from app.services.super_resolution_service import SuperResolutionService
from app.models.schemas import ImageryRequest
from app.services.copernicus_service import CopernicusService

router = APIRouter()
service = SuperResolutionService()
copernicus_service = CopernicusService()
DATA_ROOT = Path(__file__).resolve().parents[4] / "data" / "demo" / "sample"
DATA_ROOT.mkdir(parents=True, exist_ok=True)


def _demo_input() -> Path:
    path = DATA_ROOT / "sentinel2_demo_128.tif"
    if not path.exists():
        rows, cols = np.mgrid[0:128, 0:128]
        data = np.empty((3, 128, 128), dtype="uint8")
        data[0] = np.clip(68 + rows * 0.35 + cols * 0.2, 0, 255)
        data[1] = np.clip(122 + rows * 0.3 - cols * 0.1, 0, 255)
        data[2] = np.clip(78 + cols * 0.25, 0, 255)
        data[:, 36:84, 40:90] = np.array([170, 120, 80], dtype="uint8")[:, None, None]
        data[:, 16:22, :] = np.array([205, 205, 190], dtype="uint8")[:, None, None]
        data[:, :, 16:22] = np.array([205, 205, 190], dtype="uint8")[:, None, None]
        data[:, 96:102, 16:112] = np.array([195, 195, 182], dtype="uint8")[:, None, None]
        profile = {"driver": "GTiff", "height": 128, "width": 128, "count": 3,
                   "dtype": "uint8", "crs": "EPSG:3857",
                   "transform": rasterio.transform.from_origin(0, 640, 10, 10)}
        with rasterio.open(path, "w", **profile) as destination:
            destination.write(data)
            for index, name in enumerate(("red", "green", "blue"), 1):
                destination.set_band_description(index, name)
    return path


@router.post("/demo")
async def run_demo(request: SuperResolutionRequest = SuperResolutionRequest()):
    input_path = _demo_input()
    output_path = DATA_ROOT / "sentinel2_demo_srm.tif"
    try:
        return service.process(str(input_path), str(output_path), request.reference_path,
                       request.tile_size, request.overlap)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/process")
async def process(request: SuperResolutionRequest):
    input_path = Path(request.input_path) if request.input_path else _demo_input()
    if not input_path.is_file():
        raise HTTPException(status_code=404, detail="Input GeoTIFF was not found")
    output_path = input_path.with_name(input_path.stem + "_srm.tif")
    try:
        return service.process(str(input_path), str(output_path), request.reference_path,
                               request.tile_size, request.overlap)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/live")
async def process_live(request: SuperResolutionRequest):
    if request.latitude is None or request.longitude is None or not request.date:
        raise HTTPException(status_code=400, detail="latitude, longitude, and date are required")
    imagery_request = ImageryRequest(latitude=request.latitude, longitude=request.longitude,
                                     bbox=request.bbox, date=request.date,
                                     max_cloud_cover=request.max_cloud_cover)
    try:
        input_path = await copernicus_service.download_tci(imagery_request, DATA_ROOT / "live")
        output_path = input_path.with_name(input_path.stem + "_srm.tif")
        return service.process(str(input_path), str(output_path), request.reference_path,
                               request.tile_size, request.overlap)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Live Sentinel-2 processing failed: {exc}") from exc


@router.get("/files/{filename}")
async def get_file(filename: str):
    matches = [candidate for candidate in DATA_ROOT.rglob(filename) if candidate.is_file()]
    path = matches[0] if len(matches) == 1 else None
    if path is None:
        raise HTTPException(status_code=404, detail="File not found")
    media_type = "image/png" if path.suffix.lower() == ".png" else "image/tiff"
    return FileResponse(path, media_type=media_type, filename=path.name)