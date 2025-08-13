"""Train match outcome prediction model using XGBoost."""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, roc_auc_score, brier_score_loss, log_loss
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import json
from typing import Tuple, Dict, Any

from ..utils.cache import cache_to_pickle
from ..utils.io import save_pickle, save_json, load_parquet
from ..utils.paths import PROCESSED_DATA_ROOT, MODELS_ROOT, SITE_DATA


def prepare_outcome_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare features for match outcome prediction."""
    
    print("Preparing outcome prediction features...")
    
    # Create target variable (1 if higher-rated player wins, 0 otherwise)
    df['target'] = (df['elo_diff'] > 0).astype(int)
    
    # Select features for prediction
    feature_cols = [
        # Elo ratings
        'winner_elo_before', 'loser_elo_before', 'elo_diff',
        
        # Head-to-head
        'h2h_matches', 'h2h_win_pct',
        
        # Recent form
        'winner_recent_win_pct', 'loser_recent_win_pct',
        'winner_recent_surface_win_pct', 'loser_recent_surface_win_pct',
        'winner_recent_matches', 'loser_recent_matches',
        
        # Match context
        'surface', 'round', 'best_of', 'tour',
        
        # Player attributes
        'winner_age', 'loser_age', 'age_diff',
        
        # Temporal features
        'year', 'month', 'days_since_epoch'
    ]
    
    # Filter to available columns
    available_cols = [col for col in feature_cols if col in df.columns]
    features_df = df[available_cols].copy()
    
    # Handle categorical variables
    categorical_cols = ['surface', 'round', 'tour']
    label_encoders = {}
    
    for col in categorical_cols:
        if col in features_df.columns:
            le = LabelEncoder()
            features_df[col] = le.fit_transform(features_df[col].fillna('Unknown'))
            label_encoders[col] = le
    
    # Fill missing values
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns
    features_df[numeric_cols] = features_df[numeric_cols].fillna(features_df[numeric_cols].median())
    
    # Remove rows with missing target
    valid_mask = df['target'].notna()
    features_df = features_df[valid_mask]
    target = df.loc[valid_mask, 'target']
    
    print(f"Features prepared: {features_df.shape[0]} samples, {features_df.shape[1]} features")
    
    return features_df, target, label_encoders


def create_temporal_splits(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create temporal train/validation/test splits."""
    
    # Sort by date and create splits
    df_sorted = df.sort_values('date').reset_index(drop=True)
    
    # Use years for splits: 2018-2022 train, 2023 val, 2024 test
    train_mask = df_sorted['year'] <= 2022
    val_mask = df_sorted['year'] == 2023
    test_mask = df_sorted['year'] >= 2024
    
    train_idx = df_sorted[train_mask].index.values
    val_idx = df_sorted[val_mask].index.values
    test_idx = df_sorted[test_mask].index.values
    
    print(f"Temporal splits - Train: {len(train_idx)}, Val: {len(val_idx)}, Test: {len(test_idx)}")
    
    return train_idx, val_idx, test_idx


@cache_to_pickle()
def train_xgboost_model(X: pd.DataFrame, y: pd.Series, 
                       train_idx: np.ndarray, val_idx: np.ndarray) -> xgb.XGBClassifier:
    """Train XGBoost model for outcome prediction."""
    
    print("Training XGBoost model...")
    
    # Prepare training and validation sets
    X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
    X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
    
    # XGBoost parameters
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'logloss',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 500,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'early_stopping_rounds': 50,
        'verbose': False
    }
    
    # Train model
    model = xgb.XGBClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    print(f"Model trained. Best iteration: {model.best_iteration}")
    
    return model


def evaluate_model(model: xgb.XGBClassifier, X: pd.DataFrame, y: pd.Series,
                  train_idx: np.ndarray, val_idx: np.ndarray, 
                  test_idx: np.ndarray) -> Dict[str, Any]:
    """Evaluate model performance on all splits."""
    
    print("Evaluating model performance...")
    
    metrics = {}
    
    for split_name, idx in [('train', train_idx), ('val', val_idx), ('test', test_idx)]:
        if len(idx) == 0:
            continue
            
        X_split, y_split = X.iloc[idx], y.iloc[idx]
        
        # Predictions
        y_pred = model.predict(X_split)
        y_pred_proba = model.predict_proba(X_split)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_split, y_pred)
        auc = roc_auc_score(y_split, y_pred_proba)
        brier = brier_score_loss(y_split, y_pred_proba)
        logloss = log_loss(y_split, y_pred_proba)
        
        metrics[split_name] = {
            'accuracy': float(accuracy),
            'auc': float(auc),
            'brier_score': float(brier),
            'log_loss': float(logloss),
            'n_samples': len(idx)
        }
        
        print(f"{split_name.title()} - AUC: {auc:.4f}, Accuracy: {accuracy:.4f}, Brier: {brier:.4f}")
    
    return metrics


def get_feature_importance(model: xgb.XGBClassifier, feature_names: list) -> Dict[str, float]:
    """Get feature importance from trained model."""
    
    importance_scores = model.feature_importances_
    feature_importance = dict(zip(feature_names, importance_scores))
    
    # Sort by importance
    feature_importance = dict(sorted(feature_importance.items(), 
                                   key=lambda x: x[1], reverse=True))
    
    return feature_importance


def train_outcome_pipeline() -> Dict[str, Any]:
    """Complete outcome prediction training pipeline."""
    
    print("Starting outcome prediction training...")
    
    # Load processed matches
    matches_path = PROCESSED_DATA_ROOT / 'matches_with_features.parquet'
    if not matches_path.exists():
        print("Processed matches not found. Run feature engineering first.")
        return {}
    
    matches_df = load_parquet(matches_path)
    
    # Prepare features
    X, y, label_encoders = prepare_outcome_features(matches_df)
    
    # Create temporal splits
    train_idx, val_idx, test_idx = create_temporal_splits(matches_df.loc[X.index])
    
    # Train model
    model = train_xgboost_model(X, y, train_idx, val_idx)
    
    # Evaluate model
    metrics = evaluate_model(model, X, y, train_idx, val_idx, test_idx)
    
    # Get feature importance
    feature_importance = get_feature_importance(model, X.columns.tolist())
    
    # Save model and artifacts
    model_path = MODELS_ROOT / 'outcome_xgb.pkl'
    encoders_path = MODELS_ROOT / 'label_encoders.pkl'
    metrics_path = MODELS_ROOT / 'outcome_metrics.json'
    
    save_pickle(model, model_path)
    save_pickle(label_encoders, encoders_path)
    save_json(metrics, metrics_path)
    
    # Save for website
    site_metrics = {
        'model_type': 'XGBoost',
        'metrics': metrics,
        'feature_importance': feature_importance,
        'last_updated': pd.Timestamp.now().isoformat()
    }
    
    save_json(site_metrics, SITE_DATA / 'outcome_model.json')
    
    print("✅ Outcome prediction training complete!")
    print(f"Best test AUC: {metrics.get('test', {}).get('auc', 'N/A'):.4f}")
    
    return site_metrics


if __name__ == "__main__":
    train_outcome_pipeline()