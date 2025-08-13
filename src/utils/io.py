"""I/O utilities for RallyScope project."""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from tqdm import tqdm


def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file with progress bar."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, 'wb') as f, tqdm(
            desc=dest_path.name,
            total=total_size,
            unit='B',
            unit_scale=True
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def load_csv_with_fallback(file_path: Path, **kwargs) -> Optional[pd.DataFrame]:
    """Load CSV with various encoding fallbacks."""
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding, **kwargs)
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"Error loading {file_path} with {encoding}: {e}")
            continue
    
    print(f"Failed to load {file_path} with any encoding")
    return None


def save_json(data: Any, file_path: Path) -> bool:
    """Save data as JSON."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving JSON to {file_path}: {e}")
        return False


def load_json(file_path: Path) -> Optional[Any]:
    """Load JSON data."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {e}")
        return None


def save_pickle(obj: Any, file_path: Path) -> bool:
    """Save object as pickle."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as f:
            pickle.dump(obj, f)
        return True
    except Exception as e:
        print(f"Error saving pickle to {file_path}: {e}")
        return False


def load_pickle(file_path: Path) -> Optional[Any]:
    """Load pickle object."""
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading pickle from {file_path}: {e}")
        return None


def save_parquet(df: pd.DataFrame, file_path: Path) -> bool:
    """Save DataFrame as parquet."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(file_path, index=False)
        return True
    except Exception as e:
        print(f"Error saving parquet to {file_path}: {e}")
        return False


def load_parquet(file_path: Path) -> Optional[pd.DataFrame]:
    """Load parquet as DataFrame."""
    try:
        return pd.read_parquet(file_path)
    except Exception as e:
        print(f"Error loading parquet from {file_path}: {e}")
        return None