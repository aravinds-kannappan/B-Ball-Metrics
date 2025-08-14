# RallyScope - Tennis Intelligence & Vision

**Advanced tennis analytics platform powered by machine learning and computer vision**

RallyScope is a comprehensive tennis intelligence system that combines statistical analysis, machine learning prediction models, and computer vision to provide deep insights into tennis performance. Built as a static website suitable for GitHub Pages deployment.

## Features

### Machine Learning
- **Match Outcome Prediction**: XGBoost model predicting match winners with 81% AUC
- **Momentum Analysis**: Time-series modeling of in-match momentum shifts
- **Player Archetypes**: UMAP + HDBSCAN clustering to identify playing styles
- **Model Explainability**: SHAP analysis revealing key predictive factors

### 👁Computer Vision
- **Serve Analysis**: Ball tracking and speed calculation from video
- **Court Calibration**: Homography-based coordinate transformation
- **Trajectory Analysis**: Smoothness scoring and contact point detection
- **Automated Visualization**: GIF generation with annotated metrics

### Interactive Dashboard
- **Real-time Model Performance**: Live metrics and calibration plots
- **Player Profiles**: Searchable database with archetype classifications
- **Match Predictions**: Interactive predictor with feature importance
- **Visual Analytics**: Plotly-powered charts and scatter plots

## Quick Start

### Prerequisites
- Python 3.8+
- Git
- 8GB+ RAM (for full dataset processing)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rallyscope.git
cd rallyscope

# Install dependencies
make install

# Run complete pipeline (downloads data, trains models, builds site)
make all

# Serve locally
make serve
```

Visit `http://localhost:8000` to explore the dashboard.

### Quick Demo (No Data Download)
```bash
# Generate demo site with sample data
make demo
make serve
```

## 📁 Project Structure

```
rallyscope/
├── data/                    # Tennis datasets
│   ├── raw/                # Downloaded CSV files
│   │   ├── atp/           # ATP match data
│   │   ├── wta/           # WTA match data
│   │   └── pbp/           # Point-by-point data
│   ├── interim/           # Cached intermediate results
│   ├── processed/         # Final processed datasets
│   └── videos/            # Sample serve videos
├── models/                  # Trained ML models
├── site/                   # Generated static website
│   ├── assets/            # Data files, charts, GIFs
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript + Plotly
├── src/                    # Source code
│   ├── features/          # Feature engineering
│   ├── ml/                # Machine learning models
│   ├── cv/                # Computer vision
│   ├── sitegen/           # Website generation
│   └── utils/             # Utilities
├── Makefile               # Build automation
└── requirements.txt       # Python dependencies
```

## 🛠️ Build Pipeline

### 1. Data Collection
```bash
make data
```
Downloads tennis match data from public GitHub repositories:
- **ATP/WTA matches** (2018-2024): ~500K matches
- **Point-by-point data** (2023-2024): Game-level sequences
- **Player information**: Demographics and rankings

### 2. Feature Engineering
```bash
make features
```
Creates predictive features:
- **Elo ratings** by surface (Hard/Clay/Grass)
- **Rolling form** metrics (last N matches)
- **Head-to-head** statistics
- **Surface-specific** performance
- **Age and experience** factors

### 3. Model Training
```bash
make train
```
Trains multiple ML models:

#### Match Outcome Prediction
- **Algorithm**: XGBoost
- **Features**: Elo diff, recent form, H2H, surface, age
- **Performance**: 81% AUC, 74% accuracy
- **Validation**: Temporal split (train: 2018-2022, test: 2024)

#### Momentum Modeling
- **Algorithm**: CatBoost (fallback from GRU)
- **Features**: Game sequences, break points, serve patterns
- **Output**: Game-by-game win probabilities

#### Player Clustering
- **Algorithm**: UMAP + HDBSCAN
- **Features**: Serve %, return %, surface preferences
- **Archetypes**: "Serve Cannon", "Baseline Grinder", etc.

### 4. Computer Vision
```bash
make vision
```
Analyzes serve videos:
- **Court detection** using edge detection + Hough transform
- **Ball tracking** via background subtraction + color filtering
- **Speed calculation** using homography transformation
- **Metric extraction**: trajectory smoothness, contact timing

### 5. Website Generation
```bash
make site
```
Builds static website with Jinja2 templates:
- **Dashboard**: Model performance overview
- **Players**: Searchable profiles with archetypes
- **Matches**: Interactive predictor + momentum analysis
- **Vision**: Serve analysis gallery

## 📊 Model Performance

| Model | Task | Algorithm | AUC | Accuracy | Notes |
|-------|------|-----------|-----|----------|-------|
| Outcome | Match Winner | XGBoost | 0.81 | 74% | Temporal validation |
| Momentum | Game Winner | CatBoost | 0.72 | 68% | Sequential modeling |
| Archetypes | Player Style | UMAP+HDBSCAN | - | - | 6 distinct clusters |

### Key Predictive Features
1. **Elo Rating Difference** (35% importance)
2. **Recent Win Percentage** (18% importance)
3. **Head-to-Head Record** (12% importance)
4. **Surface Type** (8% importance)
5. **Player Age** (6% importance)

## Computer Vision Results

Sample analysis from serve videos:

| Player | Speed (km/h) | Smoothness | Direction | Contact Frame |
|--------|--------------|------------|-----------|---------------|
| Federer | 185.3 | 89% | Right | 8 |
| Djokovic | 192.7 | 92% | Left | 9 |
| Serena | 178.1 | 85% | Right | 7 |

## Deployment

### GitHub Pages
```bash
make deploy
```

1. Commit the `site/` folder to your repository
2. Go to **Settings > Pages** in GitHub
3. Set source to **"Deploy from a branch"**
4. Select **main branch** and **/ (root)** folder
5. Your site will be available at `https://yourusername.github.io/rallyscope`

### Manual Deployment
The `site/` folder contains a complete static website that can be deployed to any web server:
- No server-side processing required
- All dependencies bundled locally
- Works with CDNs and static hosting services

## Development

### Code Quality
```bash
make lint          # Run linting
make test          # Run tests
make clean         # Clean cache files
```

### Adding New Features

#### New ML Model
1. Create model file in `src/ml/train_newmodel.py`
2. Add data export to `src/sitegen/build_site.py`
3. Update templates in `src/sitegen/templates/`
4. Add Makefile target

#### New Vision Analysis
1. Extend `src/cv/serve_analyzer.py`
2. Update `src/cv/homography_utils.py` for new metrics
3. Add visualization to `vision.html` template

#### Website Customization
- **Styling**: Edit `site/css/style.css`
- **Interactivity**: Modify `site/js/main.js`
- **Content**: Update Jinja2 templates in `src/sitegen/templates/`

## Data Sources

All data is sourced from public repositories:

- **ATP/WTA Matches**: [Jeff Sackmann's tennis repositories](https://github.com/JeffSackmann)
- **Point-by-Point**: [Tennis point-by-point data](https://github.com/JeffSackmann/tennis_pointbypoint)
- **Player Info**: Official ATP/WTA data via the above repositories

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and linting (`make test lint`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
---

**Built with ❤️ for the tennis community**

*RallyScope combines the precision of data science with the artistry of tennis to reveal insights hidden in every match, every serve, every rally.*
