"""Download tennis datasets from GitHub repositories."""

import os
from pathlib import Path
from typing import Dict, List

from .io import download_file
from .paths import ATP_RAW, WTA_RAW, PBP_RAW


# Dataset URLs - focusing on recent years to keep size manageable
ATP_URLS = {
    'atp_matches_2018.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2018.csv',
    'atp_matches_2019.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2019.csv',
    'atp_matches_2020.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2020.csv',
    'atp_matches_2021.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2021.csv',
    'atp_matches_2022.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2022.csv',
    'atp_matches_2023.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2023.csv',
    'atp_matches_2024.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2024.csv',
    'atp_players.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_players.csv',
    'atp_rankings_current.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_rankings_current.csv'
}

WTA_URLS = {
    'wta_matches_2018.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2018.csv',
    'wta_matches_2019.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2019.csv',
    'wta_matches_2020.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2020.csv',
    'wta_matches_2021.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2021.csv',
    'wta_matches_2022.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2022.csv',
    'wta_matches_2023.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2023.csv',
    'wta_matches_2024.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_2024.csv',
    'wta_players.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_players.csv',
    'wta_rankings_current.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_rankings_current.csv'
}

# Point-by-point data (smaller subset)
PBP_URLS = {
    'atp_matches_2023_pbp.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_pointbypoint/master/matches/2023/atp_matches_2023.csv',
    'atp_matches_2024_pbp.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_pointbypoint/master/matches/2024/atp_matches_2024.csv',
    'wta_matches_2023_pbp.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_pointbypoint/master/matches/2023/wta_matches_2023.csv',
    'wta_matches_2024_pbp.csv': 'https://raw.githubusercontent.com/JeffSackmann/tennis_pointbypoint/master/matches/2024/wta_matches_2024.csv'
}


def download_atp_data() -> bool:
    """Download ATP match data."""
    print("Downloading ATP data...")
    success_count = 0
    
    for filename, url in ATP_URLS.items():
        dest_path = ATP_RAW / filename
        if dest_path.exists():
            print(f"Skipping {filename} (already exists)")
            success_count += 1
            continue
            
        if download_file(url, dest_path):
            success_count += 1
        else:
            print(f"Failed to download {filename}")
    
    print(f"ATP data: {success_count}/{len(ATP_URLS)} files downloaded")
    return success_count == len(ATP_URLS)


def download_wta_data() -> bool:
    """Download WTA match data."""
    print("Downloading WTA data...")
    success_count = 0
    
    for filename, url in WTA_URLS.items():
        dest_path = WTA_RAW / filename
        if dest_path.exists():
            print(f"Skipping {filename} (already exists)")
            success_count += 1
            continue
            
        if download_file(url, dest_path):
            success_count += 1
        else:
            print(f"Failed to download {filename}")
    
    print(f"WTA data: {success_count}/{len(WTA_URLS)} files downloaded")
    return success_count == len(WTA_URLS)


def download_pbp_data() -> bool:
    """Download point-by-point data."""
    print("Downloading point-by-point data...")
    success_count = 0
    
    for filename, url in PBP_URLS.items():
        dest_path = PBP_RAW / filename
        if dest_path.exists():
            print(f"Skipping {filename} (already exists)")
            success_count += 1
            continue
            
        if download_file(url, dest_path):
            success_count += 1
        else:
            print(f"Failed to download {filename}")
    
    print(f"PBP data: {success_count}/{len(PBP_URLS)} files downloaded")
    return success_count == len(PBP_URLS)


def download_sample_videos():
    """Create placeholder video files for demonstration."""
    print("Creating sample video placeholders...")
    
    video_files = [
        'federer_serve_2019.mp4',
        'djokovic_serve_2020.mp4', 
        'serena_serve_2018.mp4'
    ]
    
    from ..utils.paths import VIDEOS_ROOT
    VIDEOS_ROOT.mkdir(parents=True, exist_ok=True)
    
    # Create small placeholder files 
    for video_file in video_files:
        video_path = VIDEOS_ROOT / video_file
        if not video_path.exists():
            # Create tiny placeholder file
            with open(video_path, 'wb') as f:
                f.write(b'placeholder_video_data')
            print(f"Created placeholder: {video_file}")


def download_all_data() -> bool:
    """Download all tennis datasets."""
    print("Starting data download process...")
    
    # Ensure directories exist
    ATP_RAW.mkdir(parents=True, exist_ok=True)
    WTA_RAW.mkdir(parents=True, exist_ok=True)
    PBP_RAW.mkdir(parents=True, exist_ok=True)
    
    # Download each dataset
    atp_success = download_atp_data()
    wta_success = download_wta_data()
    pbp_success = download_pbp_data()
    
    # Create sample videos
    download_sample_videos()
    
    success = atp_success and wta_success and pbp_success
    
    if success:
        print("✅ All data downloaded successfully!")
    else:
        print("❌ Some downloads failed. Check the logs above.")
    
    return success


if __name__ == "__main__":
    download_all_data()