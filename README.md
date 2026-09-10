# Satellite Super-Resolution Mapping

Deep Learning-based Super-Resolution Mapping of 10m Sentinel-2 satellite imagery to generate enhanced sub-4m geospatial representations using ESRGAN and PyTorch

## Features

- Interactive map interface with MapLibre
- AOI and date selection on the existing map
- Overlapping tile inference
- GeoTIFF output with CRS, bounds, transform, band names, and nodata metadata
- Original/SR comparison and GeoTIFF downloads
- Optional PSNR/SSIM validation against a reference GeoTIFF

## Technology Stack

### Frontend
- React + TypeScript
- Vite
- MapLibre GL JS
- Tailwind CSS

### Backend
- Python + FastAPI
- Pydantic
- Copernicus Data Space integration
- Rasterio + NumPy geospatial processing

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.10+
- npm or yarn

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your API keys
3. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
4. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. Start the backend:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:5173

## SRM setup

Install backend dependencies with `py -3 -m pip install -r backend/requirements.txt`, then frontend dependencies with `npm install` in `frontend`.

Satlas documents that its ESRGAN models upscale by 4x. Its 3-band TCI contract is RGB normalized by dividing 8-bit values by 255. For 16-bit non-TCI bands, values are divided by 8160 and clipped to 0-1. This prototype uses the official 1-S2 TCI checkpoint and the upstream `SSR_RRDBNet` architecture. The checkpoint downloads automatically on the first SR request into `backend/models/`, which is outside the source package.

Set `SRM_MODEL_PATH` to use a local checkpoint outside Git, or leave it blank to use the official `SRM_CHECKPOINT_URL`. The real Satlas ESRGAN model is the default. Set `SRM_USE_BASELINE=true` only to compare against the bicubic baseline.

Live catalog search uses `COPERNICUS_CLIENT_ID` and `COPERNICUS_CLIENT_SECRET`. CDSE product download additionally requires the account credentials `COPERNICUS_USERNAME` and `COPERNICUS_PASSWORD`, because CDSE does not authorize product downloads with a client-credentials token alone. Keep these values only in `backend/secrets/.env`.

Map selection requests a 128 x 128 Sentinel-2 input tile at 10 m, and the model returns a 512 x 512 nominal 2.5 m product. Optional settings are `SRM_TILE_SIZE` (default `256`), `SRM_TILE_OVERLAP` (default `32`), `SRM_BATCH_SIZE` (default `1`), and `SRM_MAX_INPUT_PIXELS` (default `4000000`). The live fallback crops the downloaded product to the selected AOI before inference.

## Demo and validation

Start the backend with `cd backend; py -3 -m uvicorn app.main:app --reload --port 8000` and the frontend with `cd frontend; npm run dev`. Select a map location, then click **Generate Super Resolution**. The first run creates `data/demo/sample/sentinel2_demo.tif`; output is written beside it as `sentinel2_demo_srm.tif`.

For objective validation, call `POST /api/srm/process` with `reference_path` pointing to a co-registered high-resolution GeoTIFF. PSNR and SSIM are returned only when that file is available. Otherwise the UI displays: “High-resolution reference unavailable; objective accuracy metrics cannot be calculated.”


