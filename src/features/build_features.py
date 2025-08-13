"""Feature engineering pipeline for tennis match prediction."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ..utils.cache import cache_to_parquet
from ..utils.io import load_csv_with_fallback, save_parquet
from ..utils.paths import ATP_RAW, WTA_RAW, PROCESSED_DATA_ROOT


@cache_to_parquet()
def load_and_combine_matches() -> pd.DataFrame:
    """Load and combine ATP and WTA match data."""
    
    all_matches = []
    
    # Load ATP matches
    print("Loading ATP matches...")
    for year in range(2018, 2025):
        file_path = ATP_RAW / f"atp_matches_{year}.csv"
        if file_path.exists():
            df = load_csv_with_fallback(file_path)
            if df is not None:
                df['tour'] = 'ATP'
                all_matches.append(df)
    
    # Load WTA matches
    print("Loading WTA matches...")
    for year in range(2018, 2025):
        file_path = WTA_RAW / f"wta_matches_{year}.csv"
        if file_path.exists():
            df = load_csv_with_fallback(file_path)
            if df is not None:
                df['tour'] = 'WTA'
                all_matches.append(df)
    
    if not all_matches:
        raise ValueError("No match data found!")
    
    # Combine all matches
    combined_df = pd.concat(all_matches, ignore_index=True)
    
    # Standardize column names and data types
    combined_df = standardize_match_data(combined_df)
    
    print(f"Loaded {len(combined_df)} matches from {combined_df['year'].min()}-{combined_df['year'].max()}")
    
    return combined_df


def standardize_match_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize match data columns and types."""
    
    # Ensure essential columns exist
    required_cols = ['tourney_date', 'surface', 'draw_size', 'tourney_level', 
                    'winner_id', 'loser_id', 'score', 'best_of', 'round']
    
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    
    # Convert date column
    if 'tourney_date' in df.columns:
        df['date'] = pd.to_datetime(df['tourney_date'], format='%Y%m%d', errors='coerce')
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
    
    # Clean surface names
    if 'surface' in df.columns:
        df['surface'] = df['surface'].fillna('Unknown').str.title()
        surface_mapping = {
            'Hard': 'Hard',
            'Clay': 'Clay', 
            'Grass': 'Grass',
            'Carpet': 'Hard',  # Treat carpet as hard court
            'Unknown': 'Hard'
        }
        df['surface'] = df['surface'].map(surface_mapping).fillna('Hard')
    
    # Clean round names
    if 'round' in df.columns:
        df['round'] = df['round'].fillna('Unknown')
    
    # Add match duration in days since epoch (for temporal features)
    if 'date' in df.columns:
        epoch = pd.Timestamp('2000-01-01')
        df['days_since_epoch'] = (df['date'] - epoch).dt.days
    
    # Clean player IDs
    df['winner_id'] = pd.to_numeric(df['winner_id'], errors='coerce')
    df['loser_id'] = pd.to_numeric(df['loser_id'], errors='coerce')
    
    # Remove matches with missing essential data
    df = df.dropna(subset=['winner_id', 'loser_id', 'date'])
    
    return df


@cache_to_parquet()
def add_player_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add player-specific features to match data."""
    
    print("Adding player features...")
    
    # Load player info
    atp_players = load_csv_with_fallback(ATP_RAW / 'atp_players.csv') if (ATP_RAW / 'atp_players.csv').exists() else pd.DataFrame()
    wta_players = load_csv_with_fallback(WTA_RAW / 'wta_players.csv') if (WTA_RAW / 'wta_players.csv').exists() else pd.DataFrame()
    
    # Combine player data
    all_players = []
    if not atp_players.empty:
        atp_players['tour'] = 'ATP'
        all_players.append(atp_players)
    if not wta_players.empty:
        wta_players['tour'] = 'WTA'
        all_players.append(wta_players)
    
    if all_players:
        players_df = pd.concat(all_players, ignore_index=True)
        
        # Parse birth dates
        if 'dob' in players_df.columns:
            players_df['dob'] = pd.to_numeric(players_df['dob'], errors='coerce')
            players_df['birth_date'] = pd.to_datetime(players_df['dob'], format='%Y%m%d', errors='coerce')
    else:
        players_df = pd.DataFrame()
    
    # Add winner age
    if not players_df.empty:
        winner_ages = df.merge(
            players_df[['player_id', 'birth_date']], 
            left_on='winner_id', 
            right_on='player_id', 
            how='left'
        )
        winner_ages['winner_age'] = (winner_ages['date'] - winner_ages['birth_date']).dt.days / 365.25
        df['winner_age'] = winner_ages['winner_age']
        
        # Add loser age
        loser_ages = df.merge(
            players_df[['player_id', 'birth_date']], 
            left_on='loser_id', 
            right_on='player_id', 
            how='left'
        )
        loser_ages['loser_age'] = (loser_ages['date'] - loser_ages['birth_date']).dt.days / 365.25
        df['loser_age'] = loser_ages['loser_age']
        
        # Add age difference
        df['age_diff'] = df['winner_age'] - df['loser_age']
    else:
        df['winner_age'] = None
        df['loser_age'] = None
        df['age_diff'] = None
    
    return df


@cache_to_parquet()
def add_head_to_head_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add head-to-head statistics."""
    
    print("Adding head-to-head features...")
    
    # Sort by date to compute rolling H2H
    df = df.sort_values('date').reset_index(drop=True)
    
    # Initialize H2H columns
    df['h2h_wins'] = 0
    df['h2h_losses'] = 0
    df['h2h_matches'] = 0
    df['h2h_win_pct'] = 0.5
    
    # Track H2H records
    h2h_records = {}
    
    for idx, row in df.iterrows():
        winner_id = row['winner_id']
        loser_id = row['loser_id']
        
        # Create sorted tuple for consistent key
        match_key = tuple(sorted([winner_id, loser_id]))
        
        if match_key not in h2h_records:
            h2h_records[match_key] = {'matches': 0, 'wins': {winner_id: 0, loser_id: 0}}
        
        # Get current H2H stats before this match
        h2h_data = h2h_records[match_key]
        total_matches = h2h_data['matches']
        winner_wins = h2h_data['wins'].get(winner_id, 0)
        
        df.loc[idx, 'h2h_matches'] = total_matches
        df.loc[idx, 'h2h_wins'] = winner_wins
        df.loc[idx, 'h2h_losses'] = total_matches - winner_wins
        
        if total_matches > 0:
            df.loc[idx, 'h2h_win_pct'] = winner_wins / total_matches
        else:
            df.loc[idx, 'h2h_win_pct'] = 0.5
        
        # Update H2H record with this match result
        h2h_records[match_key]['matches'] += 1
        h2h_records[match_key]['wins'][winner_id] += 1
    
    return df


@cache_to_parquet()
def add_rolling_form_features(df: pd.DataFrame, window_size: int = 10) -> pd.DataFrame:
    """Add rolling form statistics."""
    
    print(f"Adding rolling form features (window={window_size})...")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Initialize form columns
    form_cols = ['recent_wins', 'recent_matches', 'recent_win_pct', 
                'recent_surface_wins', 'recent_surface_matches', 'recent_surface_win_pct']
    
    for col in form_cols:
        df[f'winner_{col}'] = 0.0
        df[f'loser_{col}'] = 0.0
    
    # Track form for each player
    player_matches = {}
    
    for idx, row in df.iterrows():
        winner_id = row['winner_id']
        loser_id = row['loser_id']
        surface = row['surface']
        match_date = row['date']
        
        # Initialize player records if needed
        for player_id in [winner_id, loser_id]:
            if player_id not in player_matches:
                player_matches[player_id] = []
        
        # Calculate form for winner (before this match)
        winner_recent = [m for m in player_matches[winner_id] 
                        if (match_date - m['date']).days <= 365][-window_size:]
        
        winner_wins = sum(1 for m in winner_recent if m['won'])
        winner_total = len(winner_recent)
        winner_surface_matches = [m for m in winner_recent if m['surface'] == surface]
        winner_surface_wins = sum(1 for m in winner_surface_matches if m['won'])
        winner_surface_total = len(winner_surface_matches)
        
        df.loc[idx, 'winner_recent_wins'] = winner_wins
        df.loc[idx, 'winner_recent_matches'] = winner_total
        df.loc[idx, 'winner_recent_win_pct'] = winner_wins / winner_total if winner_total > 0 else 0.5
        df.loc[idx, 'winner_recent_surface_wins'] = winner_surface_wins
        df.loc[idx, 'winner_recent_surface_matches'] = winner_surface_total
        df.loc[idx, 'winner_recent_surface_win_pct'] = (winner_surface_wins / winner_surface_total 
                                                       if winner_surface_total > 0 else 0.5)
        
        # Calculate form for loser (before this match)
        loser_recent = [m for m in player_matches[loser_id] 
                       if (match_date - m['date']).days <= 365][-window_size:]
        
        loser_wins = sum(1 for m in loser_recent if m['won'])
        loser_total = len(loser_recent)
        loser_surface_matches = [m for m in loser_recent if m['surface'] == surface]
        loser_surface_wins = sum(1 for m in loser_surface_matches if m['won'])
        loser_surface_total = len(loser_surface_matches)
        
        df.loc[idx, 'loser_recent_wins'] = loser_wins
        df.loc[idx, 'loser_recent_matches'] = loser_total
        df.loc[idx, 'loser_recent_win_pct'] = loser_wins / loser_total if loser_total > 0 else 0.5
        df.loc[idx, 'loser_recent_surface_wins'] = loser_surface_wins
        df.loc[idx, 'loser_recent_surface_matches'] = loser_surface_total
        df.loc[idx, 'loser_recent_surface_win_pct'] = (loser_surface_wins / loser_surface_total 
                                                      if loser_surface_total > 0 else 0.5)
        
        # Add this match to player histories
        player_matches[winner_id].append({
            'date': match_date,
            'surface': surface,
            'won': True,
            'opponent': loser_id
        })
        
        player_matches[loser_id].append({
            'date': match_date,
            'surface': surface,
            'won': False,
            'opponent': winner_id
        })
    
    return df


def build_features_pipeline() -> pd.DataFrame:
    """Run complete feature engineering pipeline."""
    
    print("Starting feature engineering pipeline...")
    
    # Load and combine match data
    matches_df = load_and_combine_matches()
    
    # Add player features
    matches_df = add_player_features(matches_df)
    
    # Add head-to-head features
    matches_df = add_head_to_head_features(matches_df)
    
    # Add rolling form features
    matches_df = add_rolling_form_features(matches_df)
    
    # Save processed features
    output_path = PROCESSED_DATA_ROOT / 'matches_with_features.parquet'
    save_parquet(matches_df, output_path)
    
    print(f"Feature engineering complete! Saved to {output_path}")
    print(f"Final dataset shape: {matches_df.shape}")
    print(f"Features: {list(matches_df.columns)}")
    
    return matches_df


if __name__ == "__main__":
    build_features_pipeline()