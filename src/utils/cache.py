"""Caching utilities for RallyScope project."""

import hashlib
import pickle
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd

from .paths import INTERIM_DATA_ROOT


def hash_args(*args, **kwargs) -> str:
    """Create hash from function arguments."""
    combined = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(combined.encode()).hexdigest()


def cache_to_parquet(cache_dir: Path = INTERIM_DATA_ROOT):
    """Decorator to cache DataFrame results to parquet."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache filename
            func_name = func.__name__
            args_hash = hash_args(*args, **kwargs)
            cache_file = cache_dir / f"{func_name}_{args_hash}.parquet"
            
            # Try to load from cache
            if cache_file.exists():
                try:
                    print(f"Loading cached result for {func_name}")
                    return pd.read_parquet(cache_file)
                except Exception as e:
                    print(f"Cache load failed: {e}")
            
            # Compute result
            print(f"Computing {func_name}...")
            result = func(*args, **kwargs)
            
            # Save to cache if result is DataFrame
            if isinstance(result, pd.DataFrame):
                try:
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    result.to_parquet(cache_file, index=False)
                    print(f"Cached result to {cache_file}")
                except Exception as e:
                    print(f"Cache save failed: {e}")
            
            return result
        return wrapper
    return decorator


def cache_to_pickle(cache_dir: Path = INTERIM_DATA_ROOT):
    """Decorator to cache any object results to pickle."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache filename
            func_name = func.__name__
            args_hash = hash_args(*args, **kwargs)
            cache_file = cache_dir / f"{func_name}_{args_hash}.pkl"
            
            # Try to load from cache
            if cache_file.exists():
                try:
                    print(f"Loading cached result for {func_name}")
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
                except Exception as e:
                    print(f"Cache load failed: {e}")
            
            # Compute result
            print(f"Computing {func_name}...")
            result = func(*args, **kwargs)
            
            # Save to cache
            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
                print(f"Cached result to {cache_file}")
            except Exception as e:
                print(f"Cache save failed: {e}")
            
            return result
        return wrapper
    return decorator


def clear_cache(cache_dir: Path = INTERIM_DATA_ROOT, pattern: str = "*"):
    """Clear cached files matching pattern."""
    cache_files = list(cache_dir.glob(pattern))
    for file_path in cache_files:
        try:
            file_path.unlink()
            print(f"Removed {file_path}")
        except Exception as e:
            print(f"Failed to remove {file_path}: {e}")
    
    print(f"Cleared {len(cache_files)} cached files")


def get_cache_info(cache_dir: Path = INTERIM_DATA_ROOT) -> dict:
    """Get information about cached files."""
    cache_files = list(cache_dir.glob("*"))
    
    info = {
        'total_files': len(cache_files),
        'total_size_mb': sum(f.stat().st_size for f in cache_files) / 1024 / 1024,
        'files_by_type': {}
    }
    
    for file_path in cache_files:
        ext = file_path.suffix
        if ext not in info['files_by_type']:
            info['files_by_type'][ext] = {'count': 0, 'size_mb': 0}
        
        info['files_by_type'][ext]['count'] += 1
        info['files_by_type'][ext]['size_mb'] += file_path.stat().st_size / 1024 / 1024
    
    return info