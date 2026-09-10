import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "secrets", ".env"))


class Settings:
    """Application settings"""
    
    # Demo Mode
    demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() == "true"
    
    # API Keys
    copernicus_client_id: Optional[str] = os.getenv("COPERNICUS_CLIENT_ID")
    copernicus_client_secret: Optional[str] = os.getenv("COPERNICUS_CLIENT_SECRET")
    copernicus_username: Optional[str] = os.getenv("COPERNICUS_USERNAME")
    copernicus_password: Optional[str] = os.getenv("COPERNICUS_PASSWORD")
    
    # Server Configuration
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port: int = int(os.getenv("FRONTEND_PORT", "5173"))
    
    # Change Detection Service
    change_detection_api_url: Optional[str] = os.getenv("CHANGE_DETECTION_API_URL")
    change_detection_api_key: Optional[str] = os.getenv("CHANGE_DETECTION_API_KEY")

    # Super-resolution configuration. Checkpoints are intentionally kept outside Git.
    srm_model_path: Optional[str] = os.getenv("SRM_MODEL_PATH")
    srm_checkpoint_url: str = os.getenv(
        "SRM_CHECKPOINT_URL",
        "https://storage.googleapis.com/satlas-satellite-super-resolution/esrgan_1S2.pth",
    )
    srm_use_baseline: bool = os.getenv("SRM_USE_BASELINE", "false").lower() == "true"
    srm_instance_id: Optional[str] = os.getenv("SH_INSTANCE_ID")
    srm_tile_size: int = int(os.getenv("SRM_TILE_SIZE", "256"))
    srm_tile_overlap: int = int(os.getenv("SRM_TILE_OVERLAP", "32"))
    srm_batch_size: int = int(os.getenv("SRM_BATCH_SIZE", "1"))
    srm_max_input_pixels: int = int(os.getenv("SRM_MAX_INPUT_PIXELS", "4000000"))


settings = Settings()