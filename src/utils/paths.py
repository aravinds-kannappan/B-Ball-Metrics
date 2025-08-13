"""Path utilities for RallyScope project."""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
RAW_DATA_ROOT = DATA_ROOT / "raw"
INTERIM_DATA_ROOT = DATA_ROOT / "interim"
PROCESSED_DATA_ROOT = DATA_ROOT / "processed"
VIDEOS_ROOT = DATA_ROOT / "videos"
MODELS_ROOT = PROJECT_ROOT / "models"
SITE_ROOT = PROJECT_ROOT / "site"
ASSETS_ROOT = SITE_ROOT / "assets"
NOTEBOOKS_ROOT = PROJECT_ROOT / "notebooks"

# Data subdirectories
ATP_RAW = RAW_DATA_ROOT / "atp"
WTA_RAW = RAW_DATA_ROOT / "wta"
PBP_RAW = RAW_DATA_ROOT / "pbp"

# Site subdirectories
SITE_DATA = ASSETS_ROOT / "data"
SITE_MATCHES = ASSETS_ROOT / "matches"
SITE_VISION = ASSETS_ROOT / "vision"

def ensure_dirs():
    """Ensure all necessary directories exist."""
    dirs = [
        DATA_ROOT, RAW_DATA_ROOT, INTERIM_DATA_ROOT, PROCESSED_DATA_ROOT,
        VIDEOS_ROOT, MODELS_ROOT, SITE_ROOT, ASSETS_ROOT, NOTEBOOKS_ROOT,
        ATP_RAW, WTA_RAW, PBP_RAW, SITE_DATA, SITE_MATCHES, SITE_VISION
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)