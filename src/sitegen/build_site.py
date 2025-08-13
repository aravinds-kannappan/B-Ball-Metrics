"""Build static website for RallyScope using Jinja2 templates."""

import pandas as pd
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import shutil
from typing import Dict, Any, Optional

from ..utils.io import load_json, save_json
from ..utils.paths import SITE_ROOT, SITE_DATA, ASSETS_ROOT
from ..utils.paths import PROJECT_ROOT


class SiteBuilder:
    """Build static website for RallyScope."""
    
    def __init__(self):
        self.templates_dir = PROJECT_ROOT / "src" / "sitegen" / "templates"
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        
        # Add custom filters
        self.env.filters['round'] = self._round_filter
        self.env.filters['tojson'] = json.dumps
        
        self.data_cache = {}
    
    def _round_filter(self, value, decimals=2):
        """Jinja2 filter for rounding numbers."""
        try:
            return round(float(value), decimals)
        except (ValueError, TypeError):
            return value
    
    def load_data_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load data file with caching."""
        if filename in self.data_cache:
            return self.data_cache[filename]
        
        data_path = SITE_DATA / filename
        data = load_json(data_path)
        
        if data:
            self.data_cache[filename] = data
        
        return data
    
    def get_template_context(self) -> Dict[str, Any]:
        """Get context data for templates."""
        
        # Load all data files
        outcome_model = self.load_data_file('outcome_model.json') or {}
        momentum_model = self.load_data_file('momentum_model.json') or {}
        player_archetypes = self.load_data_file('player_archetypes.json') or {}
        model_explanations = self.load_data_file('model_explanations.json') or {}
        vision_analysis = self.load_data_file('vision_analysis.json') or {}
        
        # Extract key metrics
        outcome_metrics = outcome_model.get('metrics', {})
        feature_importance = outcome_model.get('feature_importance', {})
        top_features = list(feature_importance.keys())[:10] if feature_importance else []
        
        # Player data
        archetypes = player_archetypes.get('archetypes', {})
        player_profiles = player_archetypes.get('player_profiles', [])
        embedding_coords = player_archetypes.get('embedding_coords', {})
        
        # Model insights
        model_insights = model_explanations.get('insights', {}).get('insights', [])
        
        # Vision analysis
        vision_stats = {
            'total_videos': vision_analysis.get('total_videos', 0),
            'successful_analyses': vision_analysis.get('successful_analyses', 0),
            'average_speed': vision_analysis.get('average_speed', 0)
        }
        
        vision_results = vision_analysis.get('individual_results', [])
        
        # Sample matches from momentum model
        sample_matches = {}
        if momentum_model.get('sample_matches'):
            for match_id in momentum_model['sample_matches'][:5]:  # Limit to 5 matches
                match_data_path = ASSETS_ROOT / 'matches' / f'{match_id}_momentum.json'
                match_data = load_json(match_data_path)
                if match_data:
                    sample_matches[match_id] = match_data
        
        # Compile context
        context = {
            # Model metrics
            'outcome_metrics': outcome_metrics,
            'feature_importance': feature_importance,
            'top_features': top_features,
            
            # Player data
            'archetypes': archetypes,
            'player_profiles': player_profiles,
            'embedding_coords': embedding_coords,
            'total_players': len(player_profiles),
            
            # Match data
            'sample_matches': sample_matches,
            'model_insights': model_insights,
            
            # Vision analysis
            'vision_stats': vision_stats,
            'vision_results': vision_results,
            
            # Meta information
            'last_model_update': outcome_model.get('last_updated', 'N/A'),
            'latest_data_date': 'December 2024',
            'total_matches': 'N/A'  # Would be calculated from actual data
        }
        
        return context
    
    def build_page(self, template_name: str, output_name: str, 
                   additional_context: Dict[str, Any] = None) -> bool:
        """Build a single page."""
        
        try:
            template = self.env.get_template(template_name)
            
            # Get base context
            context = self.get_template_context()
            
            # Add additional context if provided
            if additional_context:
                context.update(additional_context)
            
            # Render template
            rendered = template.render(**context)
            
            # Write to output file
            output_path = SITE_ROOT / output_name
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered)
            
            print(f"Built {output_name}")
            return True
            
        except Exception as e:
            print(f"Error building {output_name}: {e}")
            return False
    
    def copy_static_assets(self) -> bool:
        """Copy static assets (CSS, JS, Plotly) to site directory."""
        
        try:
            # Ensure directories exist
            (SITE_ROOT / 'css').mkdir(exist_ok=True)
            (SITE_ROOT / 'js').mkdir(exist_ok=True)
            
            # Copy CSS and JS files (they should already be in site/ directory)
            print("Static assets already in place")
            
            # Download Plotly.js if not present
            plotly_path = SITE_ROOT / 'js' / 'plotly.min.js'
            if not plotly_path.exists():
                self.download_plotly(plotly_path)
            
            return True
            
        except Exception as e:
            print(f"Error copying static assets: {e}")
            return False
    
    def download_plotly(self, output_path: Path) -> bool:
        """Download Plotly.js library."""
        
        try:
            import requests
            
            print("Downloading Plotly.js...")
            url = "https://cdn.plot.ly/plotly-2.27.0.min.js"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"Downloaded Plotly.js to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error downloading Plotly.js: {e}")
            
            # Create a placeholder if download fails
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('// Plotly.js placeholder - replace with actual library\nconsole.log("Plotly.js placeholder");')
            
            return False
    
    def create_sample_data_files(self) -> bool:
        """Create sample data files if they don't exist."""
        
        try:
            SITE_DATA.mkdir(parents=True, exist_ok=True)
            
            # Sample outcome model data
            outcome_model_path = SITE_DATA / 'outcome_model.json'
            if not outcome_model_path.exists():
                sample_outcome = {
                    'model_type': 'XGBoost',
                    'metrics': {
                        'train': {'auc': 0.85, 'accuracy': 0.78, 'brier_score': 0.18, 'n_samples': 12000},
                        'val': {'auc': 0.82, 'accuracy': 0.75, 'brier_score': 0.19, 'n_samples': 2000},
                        'test': {'auc': 0.81, 'accuracy': 0.74, 'brier_score': 0.20, 'n_samples': 2500}
                    },
                    'feature_importance': {
                        'elo_diff': 0.35,
                        'winner_recent_win_pct': 0.18,
                        'h2h_win_pct': 0.12,
                        'surface_encoded': 0.08,
                        'winner_age': 0.06,
                        'loser_recent_win_pct': 0.05,
                        'winner_recent_surface_win_pct': 0.04,
                        'h2h_matches': 0.03,
                        'age_diff': 0.03,
                        'round_encoded': 0.02
                    },
                    'last_updated': pd.Timestamp.now().isoformat()
                }
                save_json(sample_outcome, outcome_model_path)
            
            # Sample player archetypes
            archetypes_path = SITE_DATA / 'player_archetypes.json'
            if not archetypes_path.exists():
                sample_archetypes = {
                    'archetypes': {
                        'Serve Cannon': {
                            'count': 45,
                            'avg_win_percentage': 0.68,
                            'avg_service_hold_rate': 0.85,
                            'avg_return_game_win_rate': 0.22,
                            'surface_preferences': {'hard': 0.72, 'clay': 0.65, 'grass': 0.78},
                            'avg_age': 28.5
                        },
                        'Baseline Grinder': {
                            'count': 78,
                            'avg_win_percentage': 0.62,
                            'avg_service_hold_rate': 0.72,
                            'avg_return_game_win_rate': 0.31,
                            'surface_preferences': {'hard': 0.65, 'clay': 0.75, 'grass': 0.58},
                            'avg_age': 26.8
                        },
                        'All-Court Elite': {
                            'count': 23,
                            'avg_win_percentage': 0.78,
                            'avg_service_hold_rate': 0.82,
                            'avg_return_game_win_rate': 0.35,
                            'surface_preferences': {'hard': 0.80, 'clay': 0.76, 'grass': 0.78},
                            'avg_age': 29.2
                        }
                    },
                    'player_profiles': [],  # Would be populated with actual player data
                    'embedding_coords': {'x': [], 'y': [], 'labels': []},
                    'last_updated': pd.Timestamp.now().isoformat()
                }
                save_json(sample_archetypes, archetypes_path)
            
            # Sample model explanations
            explanations_path = SITE_DATA / 'model_explanations.json'
            if not explanations_path.exists():
                sample_explanations = {
                    'insights': {
                        'insights': [
                            'Player Elo rating differences are the strongest predictor of match outcomes',
                            'Recent form on specific surfaces significantly impacts win probability',
                            'Head-to-head history becomes more important in closely matched players',
                            'Age differences matter most when one player is significantly older',
                            'Tournament surface type influences prediction accuracy'
                        ]
                    },
                    'last_updated': pd.Timestamp.now().isoformat()
                }
                save_json(sample_explanations, explanations_path)
            
            # Sample vision analysis (imported from serve_analyzer.py)
            vision_path = SITE_DATA / 'vision_analysis.json'
            if not vision_path.exists():
                from ..cv.serve_analyzer import create_sample_analysis_results
                sample_vision = create_sample_analysis_results()
                save_json(sample_vision, vision_path)
            
            print("Sample data files created")
            return True
            
        except Exception as e:
            print(f"Error creating sample data files: {e}")
            return False
    
    def build_all_pages(self) -> bool:
        """Build all website pages."""
        
        print("Building RallyScope static website...")
        
        # Ensure output directory exists
        SITE_ROOT.mkdir(parents=True, exist_ok=True)
        
        # Create sample data if needed
        self.create_sample_data_files()
        
        # Copy static assets
        self.copy_static_assets()
        
        # Build pages
        pages = [
            ('index.html', 'index.html'),
            ('players.html', 'players.html'),
            ('matches.html', 'matches.html'),
            ('vision.html', 'vision.html')
        ]
        
        success = True
        for template_name, output_name in pages:
            if not self.build_page(template_name, output_name):
                success = False
        
        if success:
            print("✅ Website build complete!")
            print(f"Site built in: {SITE_ROOT}")
            print("To serve locally: python -m http.server 8000")
            print("For GitHub Pages: commit the site/ folder")
        else:
            print("❌ Website build failed!")
        
        return success


def build_website() -> bool:
    """Build the complete RallyScope website."""
    builder = SiteBuilder()
    return builder.build_all_pages()


if __name__ == "__main__":
    build_website()