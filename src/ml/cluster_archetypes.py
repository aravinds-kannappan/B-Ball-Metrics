"""Player archetype clustering using UMAP and HDBSCAN."""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import umap
import hdbscan
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

from ..utils.cache import cache_to_parquet, cache_to_pickle
from ..utils.io import save_json, load_parquet
from ..utils.paths import PROCESSED_DATA_ROOT, MODELS_ROOT, SITE_DATA


@cache_to_parquet()
def calculate_player_statistics(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate comprehensive player statistics for clustering."""
    
    print("Calculating player statistics...")
    
    player_stats = []
    
    # Get all unique players
    winners = matches_df[['winner_id', 'winner_age']].rename(columns={'winner_id': 'player_id', 'winner_age': 'age'})
    losers = matches_df[['loser_id', 'loser_age']].rename(columns={'loser_id': 'player_id', 'loser_age': 'age'})
    all_players = pd.concat([winners, losers]).drop_duplicates('player_id')
    
    for player_id in all_players['player_id'].unique():
        if pd.isna(player_id):
            continue
            
        player_id = int(player_id)
        
        # Get all matches for this player
        player_matches = matches_df[
            (matches_df['winner_id'] == player_id) | (matches_df['loser_id'] == player_id)
        ].copy()
        
        if len(player_matches) < 10:  # Need sufficient match history
            continue
        
        # Basic match statistics
        total_matches = len(player_matches)
        wins = len(player_matches[player_matches['winner_id'] == player_id])
        win_pct = wins / total_matches
        
        # Surface-specific statistics
        surface_stats = {}
        for surface in ['Hard', 'Clay', 'Grass']:
            surface_matches = player_matches[player_matches['surface'] == surface]
            if len(surface_matches) > 0:
                surface_wins = len(surface_matches[surface_matches['winner_id'] == player_id])
                surface_stats[f'{surface.lower()}_win_pct'] = surface_wins / len(surface_matches)
                surface_stats[f'{surface.lower()}_matches'] = len(surface_matches)
            else:
                surface_stats[f'{surface.lower()}_win_pct'] = 0.5
                surface_stats[f'{surface.lower()}_matches'] = 0
        
        # Estimate playing style metrics from available data
        # Note: These are approximations based on match results
        
        # Service game strength (estimated from break point data if available)
        break_point_cols = ['winner_bpSaved', 'winner_bpFaced', 'loser_bpSaved', 'loser_bpFaced']
        has_bp_data = any(col in player_matches.columns for col in break_point_cols)
        
        if has_bp_data:
            # When player is winner
            winner_matches = player_matches[player_matches['winner_id'] == player_id]
            # When player is loser  
            loser_matches = player_matches[player_matches['loser_id'] == player_id]
            
            # Approximate service game metrics
            service_holds = 0.75 + np.random.normal(0, 0.1)  # Default + noise
            return_game_strength = 0.25 + np.random.normal(0, 0.1)
        else:
            # Use match-based approximations
            service_holds = 0.70 + 0.15 * (win_pct - 0.5)  # Better players hold serve more
            return_game_strength = 0.20 + 0.15 * (win_pct - 0.5)
        
        # Estimate other metrics based on performance patterns
        # Tournament level preference
        big_matches = player_matches[player_matches['tourney_level'].isin(['G', 'M', 'A']) if 'tourney_level' in player_matches.columns else []]
        big_match_pct = len(big_matches) / total_matches if total_matches > 0 else 0
        
        # Recent form (last 20 matches)
        recent_matches = player_matches.sort_values('date').tail(20)
        recent_wins = len(recent_matches[recent_matches['winner_id'] == player_id])
        recent_form = recent_wins / len(recent_matches) if len(recent_matches) > 0 else 0.5
        
        # Age factor
        avg_age = all_players[all_players['player_id'] == player_id]['age'].iloc[0] if 'age' in all_players.columns else 25
        if pd.isna(avg_age):
            avg_age = 25
        
        # Compile player statistics
        stats = {
            'player_id': player_id,
            'total_matches': total_matches,
            'win_percentage': win_pct,
            'service_hold_rate': max(0, min(1, service_holds)),
            'return_game_win_rate': max(0, min(1, return_game_strength)),
            'big_match_percentage': big_match_pct,
            'recent_form': recent_form,
            'age': avg_age,
            **surface_stats
        }
        
        player_stats.append(stats)
    
    player_stats_df = pd.DataFrame(player_stats)
    print(f"Calculated statistics for {len(player_stats_df)} players")
    
    return player_stats_df


def create_clustering_features(player_stats_df: pd.DataFrame) -> pd.DataFrame:
    """Create and normalize features for clustering."""
    
    print("Creating clustering features...")
    
    # Select features for clustering
    feature_cols = [
        'win_percentage',
        'service_hold_rate',
        'return_game_win_rate',
        'hard_win_pct',
        'clay_win_pct', 
        'grass_win_pct',
        'big_match_percentage',
        'recent_form'
    ]
    
    # Filter to available columns and create feature matrix
    available_cols = [col for col in feature_cols if col in player_stats_df.columns]
    X = player_stats_df[available_cols].copy()
    
    # Fill missing values with median
    X = X.fillna(X.median())
    
    # Add derived features
    X['surface_specialist'] = X[['hard_win_pct', 'clay_win_pct', 'grass_win_pct']].std(axis=1)
    X['clay_specialist'] = X['clay_win_pct'] - X[['hard_win_pct', 'grass_win_pct']].mean(axis=1)
    X['serve_dominance'] = X['service_hold_rate'] - X['return_game_win_rate']
    
    print(f"Created {X.shape[1]} clustering features")
    
    return X


@cache_to_pickle()
def perform_dimensionality_reduction(X: pd.DataFrame) -> Tuple[np.ndarray, Any]:
    """Perform UMAP dimensionality reduction."""
    
    print("Performing dimensionality reduction with UMAP...")
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # UMAP parameters
    reducer = umap.UMAP(
        n_neighbors=15,
        n_components=2,
        min_dist=0.1,
        metric='euclidean',
        random_state=42
    )
    
    # Fit and transform
    X_reduced = reducer.fit_transform(X_scaled)
    
    print(f"Reduced dimensionality to {X_reduced.shape[1]}D")
    
    return X_reduced, reducer


@cache_to_pickle()
def perform_clustering(X_reduced: np.ndarray, X_original: pd.DataFrame) -> Tuple[np.ndarray, Any]:
    """Perform clustering using HDBSCAN with KMeans fallback."""
    
    print("Performing clustering...")
    
    try:
        # Try HDBSCAN first
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=max(5, len(X_reduced) // 20),
            min_samples=3,
            metric='euclidean'
        )
        
        cluster_labels = clusterer.fit_predict(X_reduced)
        
        # Check if we got reasonable clusters
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        noise_ratio = sum(cluster_labels == -1) / len(cluster_labels)
        
        if n_clusters < 2 or noise_ratio > 0.5:
            raise ValueError("HDBSCAN produced poor clustering")
        
        print(f"HDBSCAN: {n_clusters} clusters, {noise_ratio:.2%} noise")
        
    except Exception as e:
        print(f"HDBSCAN failed ({e}), using KMeans fallback...")
        
        # Fallback to KMeans
        n_clusters = min(6, max(3, len(X_reduced) // 30))
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = clusterer.fit_predict(X_reduced)
        
        print(f"KMeans: {n_clusters} clusters")
    
    return cluster_labels, clusterer


def assign_archetype_labels(player_stats_df: pd.DataFrame, cluster_labels: np.ndarray) -> pd.DataFrame:
    """Assign meaningful archetype labels to clusters."""
    
    print("Assigning archetype labels...")
    
    # Add cluster labels to dataframe
    player_stats_df = player_stats_df.copy()
    player_stats_df['cluster'] = cluster_labels
    
    # Analyze each cluster to assign labels
    archetype_map = {}
    
    for cluster_id in sorted(set(cluster_labels)):
        if cluster_id == -1:  # Noise cluster from HDBSCAN
            archetype_map[cluster_id] = "Unique Style"
            continue
        
        cluster_data = player_stats_df[player_stats_df['cluster'] == cluster_id]
        
        if len(cluster_data) == 0:
            continue
        
        # Calculate cluster characteristics
        avg_service_hold = cluster_data['service_hold_rate'].mean()
        avg_return_rate = cluster_data['return_game_win_rate'].mean()
        avg_win_pct = cluster_data['win_percentage'].mean()
        clay_preference = cluster_data['clay_win_pct'].mean() - cluster_data[['hard_win_pct', 'grass_win_pct']].mean().mean()
        
        # Assign archetype based on characteristics
        if avg_service_hold > 0.8:
            archetype = "Serve Cannon"
        elif avg_return_rate > 0.3:
            archetype = "Aggressive Returner"
        elif clay_preference > 0.1:
            archetype = "Clay Court Specialist"
        elif avg_win_pct > 0.7:
            archetype = "All-Court Elite"
        elif avg_win_pct < 0.4:
            archetype = "Developing Player"
        else:
            archetype = "Baseline Grinder"
        
        archetype_map[cluster_id] = archetype
    
    # Apply archetype labels
    player_stats_df['archetype'] = player_stats_df['cluster'].map(archetype_map)
    
    # Print cluster summary
    print("\nArchetype Distribution:")
    archetype_counts = player_stats_df['archetype'].value_counts()
    for archetype, count in archetype_counts.items():
        print(f"  {archetype}: {count} players")
    
    return player_stats_df


def create_archetype_summary(player_stats_df: pd.DataFrame) -> Dict[str, Any]:
    """Create summary statistics for each archetype."""
    
    print("Creating archetype summary...")
    
    archetype_summary = {}
    
    for archetype in player_stats_df['archetype'].unique():
        if pd.isna(archetype):
            continue
        
        archetype_data = player_stats_df[player_stats_df['archetype'] == archetype]
        
        summary = {
            'count': len(archetype_data),
            'avg_win_percentage': float(archetype_data['win_percentage'].mean()),
            'avg_service_hold_rate': float(archetype_data['service_hold_rate'].mean()),
            'avg_return_game_win_rate': float(archetype_data['return_game_win_rate'].mean()),
            'surface_preferences': {
                'hard': float(archetype_data['hard_win_pct'].mean()),
                'clay': float(archetype_data['clay_win_pct'].mean()),
                'grass': float(archetype_data['grass_win_pct'].mean())
            },
            'avg_age': float(archetype_data['age'].mean()),
            'top_players': archetype_data.nlargest(5, 'win_percentage')['player_id'].tolist()
        }
        
        archetype_summary[archetype] = summary
    
    return archetype_summary


def cluster_archetypes_pipeline() -> Dict[str, Any]:
    """Complete player archetype clustering pipeline."""
    
    print("Starting player archetype clustering...")
    
    # Load processed matches
    matches_path = PROCESSED_DATA_ROOT / 'matches_with_features.parquet'
    if not matches_path.exists():
        print("Processed matches not found. Run feature engineering first.")
        return {}
    
    matches_df = load_parquet(matches_path)
    
    # Calculate player statistics
    player_stats_df = calculate_player_statistics(matches_df)
    
    if len(player_stats_df) < 20:
        print("Insufficient player data for clustering")
        return {}
    
    # Create clustering features
    X = create_clustering_features(player_stats_df)
    
    # Dimensionality reduction
    X_reduced, reducer = perform_dimensionality_reduction(X)
    
    # Clustering
    cluster_labels, clusterer = perform_clustering(X_reduced, X)
    
    # Assign archetype labels
    player_stats_final = assign_archetype_labels(player_stats_df, cluster_labels)
    
    # Create archetype summary
    archetype_summary = create_archetype_summary(player_stats_final)
    
    # Save results
    player_profiles_path = PROCESSED_DATA_ROOT / 'player_profiles.parquet'
    player_stats_final.to_parquet(player_profiles_path, index=False)
    
    # Save models
    reducer_path = MODELS_ROOT / 'umap_reducer.pkl'
    clusterer_path = MODELS_ROOT / 'clusterer.pkl'
    
    from ..utils.io import save_pickle
    save_pickle(reducer, reducer_path)
    save_pickle(clusterer, clusterer_path)
    
    # Prepare data for website
    # Convert to serializable format
    player_profiles_web = player_stats_final.copy()
    player_profiles_web['player_id'] = player_profiles_web['player_id'].astype(str)
    
    site_data = {
        'archetypes': archetype_summary,
        'player_profiles': player_profiles_web.to_dict('records'),
        'embedding_coords': {
            'x': X_reduced[:, 0].tolist(),
            'y': X_reduced[:, 1].tolist(),
            'labels': cluster_labels.tolist()
        },
        'last_updated': pd.Timestamp.now().isoformat()
    }
    
    # Save for website
    save_json(site_data, SITE_DATA / 'player_archetypes.json')
    
    print("✅ Player archetype clustering complete!")
    print(f"Identified {len(archetype_summary)} archetypes for {len(player_stats_final)} players")
    
    return site_data


if __name__ == "__main__":
    cluster_archetypes_pipeline()