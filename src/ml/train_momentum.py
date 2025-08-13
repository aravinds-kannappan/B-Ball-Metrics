"""Train momentum prediction model using CatBoost (fallback from deep learning)."""

import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, brier_score_loss
from typing import List, Dict, Any, Tuple
import json

from ..utils.cache import cache_to_parquet, cache_to_pickle
from ..utils.io import save_pickle, save_json, load_parquet, load_csv_with_fallback
from ..utils.paths import PBP_RAW, PROCESSED_DATA_ROOT, MODELS_ROOT, SITE_MATCHES


@cache_to_parquet()
def load_point_by_point_data() -> pd.DataFrame:
    """Load and process point-by-point data."""
    
    print("Loading point-by-point data...")
    
    pbp_files = []
    for file_path in PBP_RAW.glob("*_pbp.csv"):
        df = load_csv_with_fallback(file_path)
        if df is not None:
            pbp_files.append(df)
    
    if not pbp_files:
        print("No point-by-point data found, creating mock data...")
        return create_mock_momentum_data()
    
    pbp_df = pd.concat(pbp_files, ignore_index=True)
    
    # Basic processing
    if 'match_id' not in pbp_df.columns:
        pbp_df['match_id'] = pbp_df.index  # Fallback
    
    print(f"Loaded {len(pbp_df)} point-by-point records")
    return pbp_df


def create_mock_momentum_data() -> pd.DataFrame:
    """Create mock momentum data for demonstration."""
    
    print("Creating mock momentum data...")
    
    np.random.seed(42)
    n_matches = 1000
    
    mock_data = []
    
    for match_id in range(n_matches):
        # Random match parameters
        n_games = np.random.randint(12, 36)  # Typical match length
        server_changes = True
        current_server = 0  # 0 or 1
        
        # Game-level momentum features
        for game_num in range(n_games):
            # Simulate momentum features
            break_points_faced = np.random.poisson(0.3)
            break_points_saved = min(break_points_faced, np.random.binomial(break_points_faced, 0.7))
            
            # Rolling form in this match
            games_won_p1 = sum(1 for g in mock_data[-10:] if g.get('match_id') == match_id and g.get('game_winner') == 0)
            games_won_p2 = sum(1 for g in mock_data[-10:] if g.get('match_id') == match_id and g.get('game_winner') == 1)
            
            momentum_score = (games_won_p1 - games_won_p2) / max(1, games_won_p1 + games_won_p2)
            
            # Determine game winner (server has advantage)
            server_advantage = 0.65 + 0.1 * momentum_score if current_server == 0 else 0.65 - 0.1 * momentum_score
            game_winner = current_server if np.random.random() < server_advantage else 1 - current_server
            
            game_data = {
                'match_id': match_id,
                'game_num': game_num,
                'server': current_server,
                'game_winner': game_winner,
                'break_points_faced': break_points_faced,
                'break_points_saved': break_points_saved,
                'momentum_score': momentum_score,
                'games_won_p1': games_won_p1,
                'games_won_p2': games_won_p2
            }
            
            mock_data.append(game_data)
            
            # Alternate server each game
            current_server = 1 - current_server
    
    return pd.DataFrame(mock_data)


@cache_to_parquet()
def create_momentum_sequences(pbp_df: pd.DataFrame) -> pd.DataFrame:
    """Create momentum sequence features for each match."""
    
    print("Creating momentum sequences...")
    
    momentum_features = []
    
    for match_id in pbp_df['match_id'].unique():
        match_data = pbp_df[pbp_df['match_id'] == match_id].sort_values('game_num')
        
        if len(match_data) < 5:  # Skip very short matches
            continue
        
        # Calculate cumulative stats
        match_data['cumulative_p1_games'] = (match_data['game_winner'] == 0).cumsum()
        match_data['cumulative_p2_games'] = (match_data['game_winner'] == 1).cumsum()
        match_data['total_games'] = match_data['cumulative_p1_games'] + match_data['cumulative_p2_games']
        
        # Rolling momentum features (last 5 games)
        window = 5
        match_data['recent_p1_games'] = (match_data['game_winner'] == 0).rolling(window, min_periods=1).sum()
        match_data['recent_p2_games'] = (match_data['game_winner'] == 1).rolling(window, min_periods=1).sum()
        
        # Break point features
        if 'break_points_faced' in match_data.columns:
            match_data['cumulative_bp_faced'] = match_data['break_points_faced'].cumsum()
            match_data['cumulative_bp_saved'] = match_data['break_points_saved'].cumsum()
        else:
            match_data['cumulative_bp_faced'] = 0
            match_data['cumulative_bp_saved'] = 0
        
        # Momentum score (-1 to 1, where positive favors player 1)
        match_data['momentum_score'] = (
            (match_data['recent_p1_games'] - match_data['recent_p2_games']) / 
            np.maximum(1, match_data['recent_p1_games'] + match_data['recent_p2_games'])
        )
        
        # Target: will the server win the next game?
        match_data['next_game_server_wins'] = (
            match_data['game_winner'] == match_data['server']
        ).shift(-1)
        
        # Remove last game (no target)
        match_features = match_data.iloc[:-1].copy()
        
        momentum_features.append(match_features)
    
    if momentum_features:
        result_df = pd.concat(momentum_features, ignore_index=True)
        print(f"Created momentum sequences for {len(result_df)} games")
        return result_df
    else:
        print("No momentum sequences created")
        return pd.DataFrame()


def prepare_momentum_features(momentum_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare features for momentum prediction."""
    
    print("Preparing momentum prediction features...")
    
    feature_cols = [
        'game_num',
        'server',
        'cumulative_p1_games',
        'cumulative_p2_games', 
        'total_games',
        'recent_p1_games',
        'recent_p2_games',
        'momentum_score',
        'cumulative_bp_faced',
        'cumulative_bp_saved'
    ]
    
    # Filter to available columns
    available_cols = [col for col in feature_cols if col in momentum_df.columns]
    X = momentum_df[available_cols].copy()
    
    # Target variable
    y = momentum_df['next_game_server_wins'].copy()
    
    # Remove rows with missing target
    valid_mask = y.notna()
    X = X[valid_mask]
    y = y[valid_mask].astype(int)
    
    # Fill missing values
    X = X.fillna(0)
    
    print(f"Momentum features prepared: {X.shape[0]} samples, {X.shape[1]} features")
    
    return X, y


@cache_to_pickle()
def train_momentum_model(X: pd.DataFrame, y: pd.Series) -> CatBoostClassifier:
    """Train CatBoost model for momentum prediction."""
    
    print("Training momentum model...")
    
    # Split data (80/20 train/test)
    split_idx = int(0.8 * len(X))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # CatBoost parameters
    model = CatBoostClassifier(
        iterations=500,
        learning_rate=0.1,
        depth=6,
        l2_leaf_reg=3,
        random_seed=42,
        verbose=False,
        early_stopping_rounds=50
    )
    
    # Train model
    model.fit(
        X_train, y_train,
        eval_set=(X_test, y_test),
        verbose=False
    )
    
    print(f"Momentum model trained. Best iteration: {model.best_iteration_}")
    
    return model


def generate_sample_momentum_curves(model: CatBoostClassifier, 
                                  momentum_df: pd.DataFrame, 
                                  n_matches: int = 10) -> Dict[str, Any]:
    """Generate sample momentum curves for the website."""
    
    print("Generating sample momentum curves...")
    
    sample_matches = {}
    
    # Get sample matches
    match_ids = momentum_df['match_id'].unique()[:n_matches]
    
    for match_id in match_ids:
        match_data = momentum_df[momentum_df['match_id'] == match_id].sort_values('game_num')
        
        if len(match_data) < 5:
            continue
        
        # Prepare features for prediction
        X_match, _ = prepare_momentum_features(match_data)
        
        if len(X_match) == 0:
            continue
        
        # Predict momentum
        momentum_probs = model.predict_proba(X_match)[:, 1]  # Probability server wins
        
        # Create momentum curve data
        curve_data = {
            'game_numbers': match_data['game_num'].tolist(),
            'momentum_probs': momentum_probs.tolist(),
            'actual_winners': match_data['game_winner'].tolist(),
            'servers': match_data['server'].tolist(),
            'match_length': len(match_data)
        }
        
        sample_matches[f'match_{match_id}'] = curve_data
    
    print(f"Generated momentum curves for {len(sample_matches)} matches")
    
    return sample_matches


def train_momentum_pipeline() -> Dict[str, Any]:
    """Complete momentum prediction training pipeline."""
    
    print("Starting momentum prediction training...")
    
    # Load point-by-point data
    pbp_df = load_point_by_point_data()
    
    if pbp_df.empty:
        print("No momentum data available")
        return {}
    
    # Create momentum sequences
    momentum_df = create_momentum_sequences(pbp_df)
    
    if momentum_df.empty:
        print("No momentum sequences created")
        return {}
    
    # Save momentum sequences
    momentum_path = PROCESSED_DATA_ROOT / 'momentum_sequences.parquet'
    momentum_df.to_parquet(momentum_path, index=False)
    
    # Prepare features
    X, y = prepare_momentum_features(momentum_df)
    
    if len(X) == 0:
        print("No momentum features available")
        return {}
    
    # Train model
    model = train_momentum_model(X, y)
    
    # Evaluate model
    y_pred = model.predict(X)
    y_pred_proba = model.predict_proba(X)[:, 1]
    
    accuracy = accuracy_score(y, y_pred)
    auc = roc_auc_score(y, y_pred_proba) if len(np.unique(y)) > 1 else 0.5
    brier = brier_score_loss(y, y_pred_proba)
    
    metrics = {
        'accuracy': float(accuracy),
        'auc': float(auc),
        'brier_score': float(brier),
        'n_samples': len(X),
        'n_features': X.shape[1]
    }
    
    # Generate sample momentum curves
    sample_curves = generate_sample_momentum_curves(model, momentum_df)
    
    # Save model and artifacts
    model_path = MODELS_ROOT / 'momentum_catboost.pkl'
    metrics_path = MODELS_ROOT / 'momentum_metrics.json'
    
    save_pickle(model, model_path)
    save_json(metrics, metrics_path)
    
    # Save sample curves for website
    for match_id, curve_data in sample_curves.items():
        curve_path = SITE_MATCHES / f'{match_id}_momentum.json'
        save_json(curve_data, curve_path)
    
    # Save model info for website
    site_data = {
        'model_type': 'CatBoost',
        'metrics': metrics,
        'sample_matches': list(sample_curves.keys()),
        'last_updated': pd.Timestamp.now().isoformat()
    }
    
    save_json(site_data, SITE_DATA / 'momentum_model.json')
    
    print("✅ Momentum prediction training complete!")
    print(f"Model AUC: {auc:.4f}, Accuracy: {accuracy:.4f}")
    
    return site_data


if __name__ == "__main__":
    train_momentum_pipeline()