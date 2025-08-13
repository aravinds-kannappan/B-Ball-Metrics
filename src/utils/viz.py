"""Visualization utilities for RallyScope project."""

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np


def create_calibration_plot(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> go.Figure:
    """Create calibration plot for binary classifier."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    bin_centers = []
    bin_accuracies = []
    bin_counts = []
    
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = in_bin.mean()
        
        if prop_in_bin > 0:
            accuracy_in_bin = y_true[in_bin].mean()
            bin_centers.append((bin_lower + bin_upper) / 2)
            bin_accuracies.append(accuracy_in_bin)
            bin_counts.append(in_bin.sum())
    
    fig = go.Figure()
    
    # Perfect calibration line
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode='lines',
        name='Perfect Calibration',
        line=dict(dash='dash', color='gray')
    ))
    
    # Actual calibration
    fig.add_trace(go.Scatter(
        x=bin_centers, y=bin_accuracies,
        mode='markers+lines',
        name='Model Calibration',
        marker=dict(
            size=[c/max(bin_counts)*20 + 5 for c in bin_counts],
            color='blue'
        )
    ))
    
    fig.update_layout(
        title='Calibration Plot',
        xaxis_title='Mean Predicted Probability',
        yaxis_title='Fraction of Positives',
        showlegend=True
    )
    
    return fig


def create_feature_importance_plot(
    feature_names: List[str], 
    importance_values: List[float],
    title: str = "Feature Importance"
) -> go.Figure:
    """Create horizontal bar chart for feature importance."""
    
    # Sort by importance
    sorted_idx = np.argsort(importance_values)
    sorted_features = [feature_names[i] for i in sorted_idx]
    sorted_values = [importance_values[i] for i in sorted_idx]
    
    fig = go.Figure(go.Bar(
        x=sorted_values,
        y=sorted_features,
        orientation='h',
        marker=dict(color=sorted_values, colorscale='viridis')
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Importance',
        yaxis_title='Features',
        height=max(400, len(feature_names) * 20)
    )
    
    return fig


def create_elo_timeline(elo_df: pd.DataFrame, player_name: str, surface: str = None) -> go.Figure:
    """Create Elo rating timeline for a player."""
    player_data = elo_df[elo_df['player_name'] == player_name].copy()
    
    if surface:
        player_data = player_data[player_data['surface'] == surface]
    
    player_data = player_data.sort_values('date')
    
    fig = go.Figure()
    
    if surface:
        fig.add_trace(go.Scatter(
            x=player_data['date'],
            y=player_data['elo_rating'],
            mode='lines+markers',
            name=f'{surface.title()} Elo',
            line=dict(width=2)
        ))
        title = f'{player_name} - {surface.title()} Elo Rating Over Time'
    else:
        surfaces = player_data['surface'].unique()
        colors = px.colors.qualitative.Set1
        
        for i, surf in enumerate(surfaces):
            surf_data = player_data[player_data['surface'] == surf]
            fig.add_trace(go.Scatter(
                x=surf_data['date'],
                y=surf_data['elo_rating'],
                mode='lines+markers',
                name=f'{surf.title()}',
                line=dict(width=2, color=colors[i % len(colors)])
            ))
        title = f'{player_name} - Elo Rating Over Time by Surface'
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Elo Rating',
        showlegend=True
    )
    
    return fig


def create_momentum_plot(momentum_data: List[float], games: List[str]) -> go.Figure:
    """Create momentum swing plot for a match."""
    fig = go.Figure()
    
    # Create filled area plot
    fig.add_trace(go.Scatter(
        x=list(range(len(momentum_data))),
        y=momentum_data,
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(0,100,80,1)', width=2),
        name='Player A Momentum'
    ))
    
    # Add horizontal line at 0.5
    fig.add_hline(
        y=0.5, 
        line_dash="dash", 
        line_color="gray",
        annotation_text="Even"
    )
    
    fig.update_layout(
        title='Match Momentum',
        xaxis_title='Game Number',
        yaxis_title='Win Probability',
        yaxis=dict(range=[0, 1]),
        showlegend=False
    )
    
    # Add game labels if provided
    if games and len(games) == len(momentum_data):
        fig.update_xaxes(
            tickmode='array',
            tickvals=list(range(len(games))),
            ticktext=[g[:10] for g in games]  # Truncate long game descriptions
        )
    
    return fig


def create_player_archetype_scatter(
    player_df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str = 'archetype',
    size_col: Optional[str] = None
) -> go.Figure:
    """Create scatter plot for player archetypes."""
    
    fig = px.scatter(
        player_df,
        x=x_col,
        y=y_col,
        color=color_col,
        size=size_col if size_col else None,
        hover_data=['player_name'] + ([size_col] if size_col else []),
        title=f'Player Archetypes: {y_col} vs {x_col}'
    )
    
    fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig.update_layout(showlegend=True)
    
    return fig


def create_performance_radar(player_stats: Dict[str, float], player_name: str) -> go.Figure:
    """Create radar chart for player performance metrics."""
    
    categories = list(player_stats.keys())
    values = list(player_stats.values())
    
    # Normalize values to 0-1 scale for radar chart
    values_norm = [(v - min(values)) / (max(values) - min(values)) if max(values) > min(values) else 0.5 for v in values]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values_norm + [values_norm[0]],  # Close the loop
        theta=categories + [categories[0]],
        fill='toself',
        name=player_name,
        line=dict(color='blue')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        title=f'{player_name} - Performance Profile'
    )
    
    return fig