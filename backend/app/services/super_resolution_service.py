"""Small, geospatially safe SR pipeline for Satlas-compatible TCI inputs."""

from pathlib import Path
import time
from typing import Optional
from urllib.request import urlopen

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import Affine

from app.config import settings


class SatlasESRGAN:
    """Adapter for the Satlas 3-channel ESRGAN contract.

    The released Satlas repository has several ESRGAN checkpoints/configurations.
    Loading a checkpoint is deliberately isolated here so a project-specific
    generator can be supplied without changing the geospatial pipeline.
    """

    name = "Satlas ESRGAN"
    scale = 4

    def __init__(self, checkpoint: Optional[str] = None, checkpoint_url: Optional[str] = None):
        self.checkpoint = checkpoint or str(Path(__file__).resolve().parents[2] / "models" / "esrgan_1S2.pth")
        self.checkpoint_url = checkpoint_url
        self.model = None
        self.device = None

    def _ensure_model(self) -> None:
        if self.model is not None:
            return
        try:
            import torch
            from app.services.satlas_arch import SSR_RRDBNet
        except ImportError as exc:
            raise RuntimeError("torch is required for Satlas ESRGAN inference") from exc
        path = Path(self.checkpoint)
        if not path.is_file():
            if not self.checkpoint_url:
                raise RuntimeError(f"SR checkpoint does not exist: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with urlopen(self.checkpoint_url, timeout=120) as response, path.open("wb") as destination:
                    destination.write(response.read())
            except Exception as exc:
                raise RuntimeError(f"Unable to download Satlas checkpoint: {exc}") from exc
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = SSR_RRDBNet(num_in_ch=3, num_out_ch=3, scale=4, num_feat=64, num_block=23, num_grow_ch=32)
        checkpoint_data = torch.load(path, map_location="cpu", weights_only=False)
        state = checkpoint_data.get("params_ema", checkpoint_data.get("params", checkpoint_data))
        if not isinstance(state, dict):
            raise RuntimeError("Unsupported Satlas checkpoint format")
        state = {key.removeprefix("module."): value for key, value in state.items()}
        model.load_state_dict(state, strict=True)
        self.model = model.to(self.device).eval()

    def predict(self, tile: np.ndarray) -> np.ndarray:
        self._ensure_model()
        import torch
        with torch.inference_mode():
            output = self.model(torch.from_numpy(tile[None]).to(self.device))
        prediction = output.squeeze(0).detach().cpu().numpy()
        if prediction.shape[0] != 3 or not np.isfinite(prediction).all():
            raise RuntimeError("Satlas ESRGAN returned an invalid 3-band prediction")
        return prediction.clip(0, 1)


class BicubicBaseline:
    name = "Bicubic baseline"
    scale = 4

    def predict(self, tile: np.ndarray) -> np.ndarray:
        with rasterio.MemoryFile() as memory:
            profile = {"driver": "GTiff", "height": tile.shape[1], "width": tile.shape[2], "count": 3, "dtype": "float32"}
            with memory.open(**profile) as source:
                source.write(tile.astype("float32"))
                return source.read(out_shape=(3, tile.shape[1] * 4, tile.shape[2] * 4), resampling=Resampling.cubic)


class SuperResolutionService:
    def __init__(self) -> None:
        self.model = BicubicBaseline() if settings.srm_use_baseline else SatlasESRGAN(settings.srm_model_path, settings.srm_checkpoint_url)

    def process(self, input_path: str, output_path: str, reference_path: Optional[str] = None,
                tile_size: Optional[int] = None, overlap: Optional[int] = None) -> dict:
        started = time.perf_counter()
        tile_size = tile_size or settings.srm_tile_size
        overlap = overlap if overlap is not None else settings.srm_tile_overlap
        if tile_size <= 0 or overlap < 0 or overlap >= tile_size:
            raise ValueError("tile_size must be positive and overlap must be smaller than tile_size")

        with rasterio.open(input_path) as source:
            if source.count < 3:
                raise ValueError("Satlas TCI inference requires at least 3 bands (RGB order)")
            if source.width * source.height > settings.srm_max_input_pixels:
                raise ValueError(
                    f"Input tile is too large for 4x SR ({source.width}x{source.height}). "
                    "Select a smaller AOI so the downloaded 10 m tile is cropped before inference."
                )
            input_width, input_height = source.width, source.height
            input_pixel_size_x = abs(source.transform.a)
            input_pixel_size_y = abs(source.transform.e)
            profile = source.profile.copy()
            profile.update(
                height=source.height * self.model.scale,
                width=source.width * self.model.scale,
                transform=source.transform * Affine.scale(1 / self.model.scale),
                dtype="float32", count=3, compress="deflate", nodata=source.nodata,
            )
            output = np.zeros((3, profile["height"], profile["width"]), dtype="float32")
            weights = np.zeros((profile["height"], profile["width"]), dtype="float32")
            step = tile_size - overlap
            for row in range(0, source.height, step):
                for col in range(0, source.width, step):
                    height = min(tile_size, source.height - row)
                    width = min(tile_size, source.width - col)
                    tile = source.read(indexes=(1, 2, 3), window=((row, row + height), (col, col + width)),
                                       boundless=False).astype("float32")
                    if source.dtypes[0] == "uint8":
                        tile = tile / 255.0
                    elif tile.max() > 1.0:
                        tile = tile / 8160.0
                    tile = np.clip(tile, 0, 1)
                    prediction = self.model.predict(tile)[:, :height * 4, :width * 4]
                    out_row, out_col = row * 4, col * 4
                    out_height, out_width = prediction.shape[1:]
                    output[:, out_row:out_row + out_height, out_col:out_col + out_width] += prediction
                    weights[out_row:out_row + out_height, out_col:out_col + out_width] += 1
            output /= np.maximum(weights, 1)
            with rasterio.open(output_path, "w", **profile) as destination:
                destination.write(output)
                destination.set_band_description(1, "red")
                destination.set_band_description(2, "green")
                destination.set_band_description(3, "blue")

        input_preview = self._write_preview(input_path)
        output_preview = self._write_preview(output_path)
        metrics = self._metrics(output_path, reference_path)
        return {
            "input_url": "/srm/files/" + Path(input_path).name,
            "output_url": "/srm/files/" + Path(output_path).name,
            "input_preview_url": "/srm/files/" + input_preview.name,
            "output_preview_url": "/srm/files/" + output_preview.name,
            "model": self.model.name + (" (explicit baseline)" if isinstance(self.model, BicubicBaseline) else ""),
            "scale": self.model.scale,
            "input_width": input_width,
            "input_height": input_height,
            "output_width": profile["width"],
            "output_height": profile["height"],
            "input_resolution_m": round(input_pixel_size_x, 3),
            "output_resolution_m": round(input_pixel_size_x / self.model.scale, 3),
            "processing_time_seconds": round(time.perf_counter() - started, 3),
            "metrics": metrics,
            "validation_message": None if metrics else "Generated detail is inferred, not directly observed. Add a co-registered high-resolution reference to calculate PSNR and SSIM.",
        }

    def _write_preview(self, raster_path: str) -> Path:
        from PIL import Image, ImageFilter
        preview_path = Path(raster_path).with_suffix(".png")
        with rasterio.open(raster_path) as source:
            preview = source.read(indexes=(1, 2, 3), out_shape=(3, min(source.height, 1024), min(source.width, 1024)),
                                  resampling=Resampling.lanczos).astype("float32")
        if preview.max() <= 1.0:
            preview = np.clip(preview, 0, 1)
        else:
            stretched = np.empty_like(preview)
            for band in range(preview.shape[0]):
                low, high = np.percentile(preview[band], (2, 98))
                stretched[band] = np.clip((preview[band] - low) / max(high - low, 1), 0, 1)
            preview = stretched
        preview = (np.moveaxis(preview, 0, -1) * 255).astype("uint8")
        image = Image.fromarray(preview, mode="RGB")
        image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=3))
        image.save(preview_path, format="PNG")
        return preview_path

    def _metrics(self, output_path: str, reference_path: Optional[str]) -> Optional[dict]:
        if not reference_path or not Path(reference_path).is_file():
            return None
        try:
            from skimage.metrics import peak_signal_noise_ratio, structural_similarity
            with rasterio.open(output_path) as sr, rasterio.open(reference_path) as reference:
                reference_data = reference.read(out_shape=sr.shape, resampling=Resampling.bilinear).astype("float32")
                sr_data = sr.read().astype("float32")
            psnr = float(peak_signal_noise_ratio(reference_data, sr_data, data_range=1.0))
            ssim = float(structural_similarity(reference_data, sr_data, channel_axis=0, data_range=1.0))
            return {"psnr": round(psnr, 3), "ssim": round(ssim, 4)}
        except Exception:
            return None