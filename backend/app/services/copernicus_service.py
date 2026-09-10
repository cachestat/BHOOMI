from app.models.schemas import ImageryRequest, ImageryResponse
from app.config import settings
import httpx
import uuid
from pathlib import Path
import tempfile
import rasterio
import numpy as np
from rasterio.windows import Window
from rasterio.warp import transform_bounds
from rasterio.transform import Affine
from datetime import datetime, timedelta
import math
import zipfile


class CopernicusService:
    """Service for interacting with Copernicus Data Space API"""
    
    def __init__(self):
        self.base_url = "https://catalogue.dataspace.copernicus.eu"
        self.identity_url = "https://identity.dataspace.copernicus.eu"
        self.client_id = settings.copernicus_client_id
        self.client_secret = settings.copernicus_client_secret
        self.access_token = None
        self.srm_input_size = 128
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token from Copernicus"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Copernicus credentials not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.identity_url}/auth/realms/CDSE/protocol/openid-connect/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                }
            )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            return self.access_token

    async def _get_download_token(self) -> str:
        """Get the user token required by CDSE product downloads."""
        if not settings.copernicus_username or not settings.copernicus_password:
            raise ValueError(
                "Copernicus product downloads require COPERNICUS_USERNAME and "
                "COPERNICUS_PASSWORD in backend/secrets/.env"
            )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.identity_url}/auth/realms/CDSE/protocol/openid-connect/token",
                data={
                    "client_id": "cdse-public",
                    "username": settings.copernicus_username,
                    "password": settings.copernicus_password,
                    "grant_type": "password",
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]
    
    async def search_imagery(self, request: ImageryRequest):
        """Search for Sentinel imagery on Copernicus Data Space"""
        try:
            token = await self._get_access_token()
            
            bbox = request.bbox or self._get_default_bbox(request.latitude, request.longitude)
            if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                raise ValueError("Invalid AOI bounds; expected [west, south, east, north]")
            if not (-90 <= bbox[1] <= 90 and -90 <= bbox[3] <= 90 and -180 <= bbox[0] <= 180 and -180 <= bbox[2] <= 180):
                raise ValueError("AOI bounds must be valid WGS84 coordinates")
            
            polygon = f"POLYGON (({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, {bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"
            selected_date = datetime.strptime(request.date, "%Y-%m-%d")
            start_date = (selected_date - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = (selected_date + timedelta(days=30)).strftime("%Y-%m-%d")
            filter_expression = (
                "Collection/Name eq 'SENTINEL-2' and "
                f"OData.CSC.Intersects(area=geography'SRID=4326;{polygon}') and "
                f"ContentDate/Start gt {start_date}T00:00:00.000Z and "
                f"ContentDate/Start lt {end_date}T23:59:59.999Z"
            )
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/odata/v1/Products",
                    params={"$filter": filter_expression, "$orderby": "ContentDate/Start", "$top": "10"},
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.is_error:
                    detail = response.text[:500].replace("\n", " ")
                    raise RuntimeError(f"CDSE catalog returned HTTP {response.status_code}: {detail}")
                return response.json()
                
        except Exception as e:
            raise RuntimeError(f"Failed to search Copernicus imagery: {e}") from e
    
    async def get_imagery(self, request: ImageryRequest) -> ImageryResponse:
        """Get Sentinel imagery from Copernicus Data Space"""
        try:
            # First search for available imagery
            search_results = await self.search_imagery(request)
            
            if not search_results.get("value"):
                raise Exception("No imagery found for the specified criteria")
            
            # Get the first result
            product = search_results["value"][0]
            product_id = product["Id"]
            
            # Get product download URL
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/odata/v1/Products({product_id})/Nodes('$value')",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
            
            return ImageryResponse(
                image_id=product_id,
                image_url=f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value",
                date=product["ContentDate"]["Start"],
                satellite="Sentinel-2",
                bbox=request.bbox or self._get_default_bbox(request.latitude, request.longitude),
                metadata={
                    "cloud_cover": product.get("Attributes", [{}])[0].get("Value", 0),
                    "resolution": 10.0,
                    "processing_level": "L1C",
                    "product_name": product["Name"]
                }
            )
            
        except Exception as e:
            raise Exception(f"Failed to get Copernicus imagery: {str(e)}")

    async def download_tci(self, request: ImageryRequest, output_dir: Path) -> Path:
        """Request only the selected AOI as a 10 m GeoTIFF."""
        if not settings.srm_instance_id:
            return await self._download_tci_from_product(request, output_dir)
        bbox = request.bbox or self._get_default_bbox(request.latitude, request.longitude)
        selected_date = datetime.strptime(request.date, "%Y-%m-%d")
        start_date = (selected_date - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")
        end_date = (selected_date + timedelta(days=30)).strftime("%Y-%m-%dT23:59:59Z")
        width = max(32, min(512, round(abs(bbox[2] - bbox[0]) * 111320 * math.cos(math.radians(request.latitude)) / 10)))
        height = max(32, min(512, round(abs(bbox[3] - bbox[1]) * 111320 / 10)))
        evalscript = """
//VERSION=3
function setup() {
    return { input: [{ bands: ["B02", "B03", "B04"], units: "DN" }], output: { bands: 3, sampleType: "UINT16" } };
}
function evaluatePixel(sample) {
    return [sample.B04, sample.B03, sample.B02];
}
"""
        token = await self._get_download_token()
        output_dir.mkdir(parents=True, exist_ok=True)
        tif_path = output_dir / f"sentinel2_{request.date}_TCI.tif"
        payload = {
            "input": {"bounds": {"bbox": bbox}, "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {"timeRange": {"from": start_date, "to": end_date},
                                "maxCloudCoverage": request.max_cloud_cover},
            }]},
            "output": {"width": width, "height": height,
                        "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]},
            "evalscript": evalscript,
        }
        async with httpx.AsyncClient(timeout=180, follow_redirects=True) as client:
            response = await client.post("https://sh.dataspace.copernicus.eu/api/v1/process",
                                         headers={"Authorization": f"Bearer {token}"}, json=payload)
            response.raise_for_status()
            tif_path.write_bytes(response.content)
        with rasterio.open(tif_path) as source:
            if source.count != 3:
                raise ValueError("Copernicus Process API did not return the requested RGB raster")
            if not source.read().any():
                raise ValueError(
                    "Copernicus returned an empty raster for this AOI/date. "
                    "Choose another date or configure a Sentinel Hub Process API instance."
                )
        return tif_path

    async def _download_tci_from_product(self, request: ImageryRequest, output_dir: Path) -> Path:
        """Fallback for accounts without a Sentinel Hub Process API instance."""
        results = await self.search_imagery(request)
        if not results.get("value"):
            raise ValueError(
                "No Sentinel-2 imagery found within 30 days of the selected date. "
                "Choose a different date or expand the selected AOI."
            )
        products = results["value"]
        product = next((item for item in products if "_MSIL2A_" in item.get("Name", "")), products[0])
        product_id = product["Id"]
        token = await self._get_download_token()
        output_dir.mkdir(parents=True, exist_ok=True)
        request_id = uuid.uuid4().hex
        archive_path = output_dir / f"{product_id}_{request_id}.zip"
        try:
            url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
            async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
                async with client.stream("GET", url, headers={"Authorization": f"Bearer {token}"}) as response:
                    response.raise_for_status()
                    with archive_path.open("wb") as destination:
                        async for chunk in response.aiter_bytes():
                            destination.write(chunk)
            with zipfile.ZipFile(archive_path) as archive:
                band_members = self._find_10m_rgb_members(archive.namelist())
                if not band_members:
                    raise ValueError(
                        "Selected Sentinel-2 product has no 10 m RGB asset. "
                        "Expected B02, B03, and B04 at 10 m resolution."
                    )
                tif_path = output_dir / f"sentinel2_{request.date}_{request_id}_TCI.tif"
                extracted = {}
                try:
                    for band, member in band_members.items():
                        band_path = output_dir / f"sentinel2_{request.date}_{request_id}_{band}.jp2"
                        with archive.open(member) as source, band_path.open("wb") as destination:
                            destination.write(source.read())
                        extracted[band] = band_path

                    with rasterio.open(extracted["B04"]) as red:
                        profile = red.profile.copy()
                        try:
                            crop_window = self._aoi_window(request, red)
                            rgb = [red.read(1, window=crop_window, out_shape=(self.srm_input_size, self.srm_input_size), resampling=rasterio.enums.Resampling.bilinear)]
                        except Exception as exc:
                            raise ValueError(f"Unable to read Sentinel-2 B04 at 10 m: {exc}") from exc
                        for band in ("B03", "B02"):
                            try:
                                with rasterio.open(extracted[band]) as source:
                                    if source.count < 1:
                                        raise ValueError("asset contains no raster bands")
                                    rgb.append(source.read(
                                        1,
                                        window=crop_window,
                                        out_shape=(self.srm_input_size, self.srm_input_size),
                                        resampling=rasterio.enums.Resampling.bilinear,
                                    ))
                            except Exception as exc:
                                raise ValueError(f"Unable to read Sentinel-2 {band} at 10 m: {exc}") from exc
                        rgb_array = np.stack(rgb, axis=0)
                        if rgb_array.dtype != np.uint8:
                            rgb_array = np.clip(rgb_array, 0, 8160).astype("float32") / 8160.0
                        profile.update(
                            driver="GTiff", dtype=rgb_array.dtype, count=3, compress="deflate",
                            height=self.srm_input_size, width=self.srm_input_size,
                            transform=rasterio.windows.transform(crop_window, red.transform) * Affine.scale(
                                crop_window.width / self.srm_input_size,
                                crop_window.height / self.srm_input_size,
                            ),
                        )
                        with rasterio.open(tif_path, "w", **profile) as destination:
                            destination.write(rgb_array)
                finally:
                    for band_path in extracted.values():
                        band_path.unlink(missing_ok=True)
            return tif_path
        finally:
            archive_path.unlink(missing_ok=True)

    @staticmethod
    def _aoi_window(request: ImageryRequest, source: rasterio.DatasetReader) -> Window:
        """Return a bounded pixel window for the requested WGS84 AOI."""
        bbox = request.bbox or CopernicusService._get_default_bbox(request.latitude, request.longitude)
        left, bottom, right, top = transform_bounds("EPSG:4326", source.crs, *bbox, densify_pts=21)
        requested = rasterio.windows.from_bounds(left, bottom, right, top, transform=source.transform)
        clipped = requested.intersection(Window(0, 0, source.width, source.height))
        if clipped.width < 1 or clipped.height < 1:
            raise ValueError("Selected AOI does not overlap the downloaded Sentinel-2 tile")
        return Window(
            max(0, int(clipped.col_off)), max(0, int(clipped.row_off)),
            min(source.width - int(clipped.col_off), max(1, int(clipped.width))),
            min(source.height - int(clipped.row_off), max(1, int(clipped.height))),
        )

    @staticmethod
    def _find_10m_rgb_members(names: list[str]) -> dict[str, str] | None:
        """Find Sentinel-2 10 m reflectance bands when no TCI browse asset exists."""
        found = {}
        for name in names:
            upper_name = name.upper()
            for band in ("B02", "B03", "B04"):
                if band in found or not upper_name.endswith(".JP2"):
                    continue
                if f"_{band}_10M.JP2" in upper_name or upper_name.endswith(f"_{band}.JP2"):
                    found[band] = name
        return found if len(found) == 3 else None
    
    def _get_default_bbox(self, lat: float, lng: float) -> list:
        """Generate default bounding box around coordinates"""
        return [lng - 0.01, lat - 0.01, lng + 0.01, lat + 0.01]