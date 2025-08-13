"""Elo rating system for tennis players."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from collections import defaultdict

from ..utils.cache import cache_to_parquet
from ..utils.io import save_parquet
from ..utils.paths import INTERIM_DATA_ROOT


class TennisEloRating:
    """Tennis Elo rating system with surface-specific ratings."""
    
    def __init__(self, k_factor: float = 32, initial_rating: float = 1500):
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self.ratings = defaultdict(lambda: defaultdict(lambda: initial_rating))
        self.rating_history = []
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calculate expected score for player A vs player B."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update_ratings(self, winner_id: int, loser_id: int, surface: str, 
                      match_date: pd.Timestamp) -> Tuple[float, float]:
        """Update Elo ratings after a match."""
        
        # Get current ratings
        winner_rating = self.ratings[winner_id][surface]
        loser_rating = self.ratings[loser_id][surface]
        
        # Calculate expected scores
        winner_expected = self.expected_score(winner_rating, loser_rating)
        loser_expected = self.expected_score(loser_rating, winner_rating)
        
        # Update ratings (winner gets 1, loser gets 0)
        winner_new_rating = winner_rating + self.k_factor * (1 - winner_expected)
        loser_new_rating = loser_rating + self.k_factor * (0 - loser_expected)
        
        # Store updated ratings
        self.ratings[winner_id][surface] = winner_new_rating
        self.ratings[loser_id][surface] = loser_new_rating
        
        # Record history
        self.rating_history.append({
            'date': match_date,
            'player_id': winner_id,
            'surface': surface,
            'rating_before': winner_rating,
            'rating_after': winner_new_rating,
            'opponent_id': loser_id,
            'won': True
        })
        
        self.rating_history.append({
            'date': match_date,
            'player_id': loser_id,
            'surface': surface,
            'rating_before': loser_rating,
            'rating_after': loser_new_rating,
            'opponent_id': winner_id,
            'won': False
        })
        
        return winner_new_rating, loser_new_rating
    
    def get_rating(self, player_id: int, surface: str) -> float:
        """Get current rating for a player on a specific surface."""
        return self.ratings[player_id][surface]
    
    def get_rating_history_df(self) -> pd.DataFrame:
        """Convert rating history to DataFrame."""
        return pd.DataFrame(self.rating_history)


@cache_to_parquet()
def compute_elo_ratings(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Compute Elo ratings for all players across all surfaces."""
    
    print("Computing Elo ratings...")
    
    # Initialize Elo system
    elo_system = TennisEloRating(k_factor=32, initial_rating=1500)
    
    # Sort matches by date
    matches_df = matches_df.sort_values('date').reset_index(drop=True)
    
    # Track ratings before each match
    winner_elos = []
    loser_elos = []
    winner_elos_after = []
    loser_elos_after = []
    
    for _, row in matches_df.iterrows():
        winner_id = int(row['winner_id'])
        loser_id = int(row['loser_id'])
        surface = row['surface']
        match_date = row['date']
        
        # Get ratings before match
        winner_elo_before = elo_system.get_rating(winner_id, surface)
        loser_elo_before = elo_system.get_rating(loser_id, surface)
        
        winner_elos.append(winner_elo_before)
        loser_elos.append(loser_elo_before)
        
        # Update ratings
        winner_elo_after, loser_elo_after = elo_system.update_ratings(
            winner_id, loser_id, surface, match_date
        )
        
        winner_elos_after.append(winner_elo_after)
        loser_elos_after.append(loser_elo_after)
    
    # Add Elo columns to matches dataframe
    matches_df['winner_elo_before'] = winner_elos
    matches_df['loser_elo_before'] = loser_elos
    matches_df['winner_elo_after'] = winner_elos_after
    matches_df['loser_elo_after'] = loser_elos_after
    matches_df['elo_diff'] = matches_df['winner_elo_before'] - matches_df['loser_elo_before']
    
    # Get rating history
    rating_history_df = elo_system.get_rating_history_df()
    
    # Save rating history
    rating_history_path = INTERIM_DATA_ROOT / 'elo_history.parquet'
    save_parquet(rating_history_df, rating_history_path)
    
    print(f"Computed Elo ratings for {len(matches_df)} matches")
    print(f"Rating history saved to {rating_history_path}")
    
    return matches_df


@cache_to_parquet()
def create_current_ratings_table(rating_history_df: pd.DataFrame = None) -> pd.DataFrame:
    """Create current ratings table for all players."""
    
    if rating_history_df is None:
        rating_history_path = INTERIM_DATA_ROOT / 'elo_history.parquet'
        if rating_history_path.exists():
            rating_history_df = pd.read_parquet(rating_history_path)
        else:
            print("No rating history found. Run compute_elo_ratings first.")
            return pd.DataFrame()
    
    # Get most recent rating for each player-surface combination
    latest_ratings = rating_history_df.sort_values('date').groupby(['player_id', 'surface']).tail(1)
    
    # Pivot to have surfaces as columns
    current_ratings = latest_ratings.pivot_table(
        index='player_id', 
        columns='surface', 
        values='rating_after',
        fill_value=1500
    ).reset_index()
    
    # Add overall rating (average across surfaces, weighted by match count)
    rating_counts = rating_history_df.groupby(['player_id', 'surface']).size().unstack(fill_value=0)
    
    # Calculate weighted average rating
    surface_cols = ['Hard', 'Clay', 'Grass']
    available_surfaces = [col for col in surface_cols if col in current_ratings.columns]
    
    if available_surfaces:
        weights = rating_counts[available_surfaces].fillna(0)
        ratings = current_ratings[available_surfaces].fillna(1500)
        
        # Weighted average (minimum weight of 1 to avoid division by zero)
        weights = weights + 1
        current_ratings['overall_rating'] = (ratings * weights).sum(axis=1) / weights.sum(axis=1)
    else:
        current_ratings['overall_rating'] = 1500
    
    # Add match counts
    for surface in available_surfaces:
        if surface in rating_counts.columns:
            current_ratings[f'{surface.lower()}_matches'] = rating_counts[surface].fillna(0)
    
    # Sort by overall rating
    current_ratings = current_ratings.sort_values('overall_rating', ascending=False).reset_index(drop=True)
    
    print(f"Created current ratings for {len(current_ratings)} players")
    
    return current_ratings


def build_elo_pipeline(matches_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Complete Elo rating pipeline."""
    
    print("Starting Elo rating pipeline...")
    
    # Compute Elo ratings
    matches_with_elo = compute_elo_ratings(matches_df)
    
    # Create current ratings table
    current_ratings = create_current_ratings_table()
    
    # Save current ratings
    current_ratings_path = INTERIM_DATA_ROOT / 'current_elo_ratings.parquet'
    save_parquet(current_ratings, current_ratings_path)
    
    print(f"Elo pipeline complete!")
    print(f"Current ratings saved to {current_ratings_path}")
    
    return matches_with_elo, current_ratings


if __name__ == "__main__":
    # This would typically be run as part of the main pipeline
    from .build_features import build_features_pipeline
    
    matches_df = build_features_pipeline()
    matches_with_elo, current_ratings = build_elo_pipeline(matches_df)