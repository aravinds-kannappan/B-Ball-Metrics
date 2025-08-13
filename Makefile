# RallyScope - Tennis Intelligence & Vision
# Makefile for data processing, training, and site generation

.PHONY: help install data features train vision site clean deploy test lint

# Default target
help:
	@echo "RallyScope - Tennis Intelligence & Vision"
	@echo "=========================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install     Install Python dependencies"
	@echo "  data        Download and process tennis datasets"
	@echo "  features    Build feature engineering pipeline"
	@echo "  train       Train all machine learning models"
	@echo "  vision      Run computer vision analysis"
	@echo "  site        Generate static website"
	@echo "  all         Run complete pipeline (data -> features -> train -> vision -> site)"
	@echo "  clean       Clean generated files and cache"
	@echo "  deploy      Prepare for GitHub Pages deployment"
	@echo "  test        Run tests (if available)"
	@echo "  lint        Run code linting"
	@echo "  serve       Serve website locally"

# Python and pip commands
PYTHON := python3
PIP := pip3

# Project paths
SRC_DIR := src
DATA_DIR := data
MODELS_DIR := models
SITE_DIR := site

# Install dependencies
install:
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt
	@echo "✅ Dependencies installed"

# Download and process datasets
data:
	@echo "Downloading tennis datasets..."
	$(PYTHON) -m $(SRC_DIR).utils.download_data
	@echo "✅ Data download complete"

# Build features
features: data
	@echo "Building feature engineering pipeline..."
	$(PYTHON) -m $(SRC_DIR).features.build_features
	@echo "✅ Feature engineering complete"

# Train models
train: features
	@echo "Training machine learning models..."
	@echo "Training outcome prediction model..."
	$(PYTHON) -m $(SRC_DIR).ml.train_outcome
	@echo "Training momentum prediction model..."
	$(PYTHON) -m $(SRC_DIR).ml.train_momentum
	@echo "Clustering player archetypes..."
	$(PYTHON) -m $(SRC_DIR).ml.cluster_archetypes
	@echo "Generating model explanations..."
	$(PYTHON) -m $(SRC_DIR).ml.explain
	@echo "✅ Model training complete"

# Computer vision analysis
vision:
	@echo "Running computer vision analysis..."
	$(PYTHON) -m $(SRC_DIR).cv.serve_analyzer
	@echo "✅ Computer vision analysis complete"

# Generate static website
site: train vision
	@echo "Building static website..."
	$(PYTHON) -m $(SRC_DIR).sitegen.build_site
	@echo "✅ Website generation complete"

# Run complete pipeline
all: install data features train vision site
	@echo "🎾 RallyScope pipeline complete!"
	@echo "Website available in: $(SITE_DIR)/"
	@echo "To serve locally: make serve"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf $(DATA_DIR)/interim/*
	rm -rf $(DATA_DIR)/processed/*
	rm -rf $(MODELS_DIR)/*.pkl
	rm -rf $(MODELS_DIR)/*.json
	rm -rf $(SITE_DIR)/assets/data/*
	rm -rf $(SITE_DIR)/assets/matches/*
	rm -rf $(SITE_DIR)/assets/vision/*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Prepare for GitHub Pages deployment
deploy: site
	@echo "Preparing for GitHub Pages deployment..."
	@if [ ! -f "$(SITE_DIR)/index.html" ]; then \
		echo "❌ Site not built. Run 'make site' first."; \
		exit 1; \
	fi
	@echo "Site ready for GitHub Pages deployment"
	@echo "1. Commit the $(SITE_DIR)/ folder to your repository"
	@echo "2. Go to Settings > Pages in your GitHub repository"
	@echo "3. Set source to 'Deploy from a branch'"
	@echo "4. Select 'main' branch and '/ (root)' folder"
	@echo "5. Set custom domain if desired"

# Serve website locally
serve:
	@if [ -f "$(SITE_DIR)/index.html" ]; then \
		echo "Serving website at http://localhost:8000"; \
		cd $(SITE_DIR) && $(PYTHON) -m http.server 8000; \
	else \
		echo "❌ Site not built. Run 'make site' first."; \
	fi

# Run tests (placeholder)
test:
	@echo "Running tests..."
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -v; \
	else \
		echo "pytest not installed. Skipping tests."; \
	fi

# Code linting
lint:
	@echo "Running code linting..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 $(SRC_DIR)/ --max-line-length=100 --ignore=E501,W503; \
	else \
		echo "flake8 not installed. Skipping linting."; \
	fi
	@if command -v black >/dev/null 2>&1; then \
		black --check $(SRC_DIR)/; \
	else \
		echo "black not installed. Skipping formatting check."; \
	fi

# Development targets
dev-install: install
	@echo "Installing development dependencies..."
	$(PIP) install pytest flake8 black jupyter
	@echo "✅ Development environment ready"

# Quick demo with sample data
demo:
	@echo "Running RallyScope demo with sample data..."
	$(PYTHON) -m $(SRC_DIR).sitegen.build_site
	@echo "✅ Demo site generated with sample data"
	@echo "Run 'make serve' to view the demo"

# Check system requirements
check:
	@echo "Checking system requirements..."
	@$(PYTHON) --version
	@$(PIP) --version
	@if command -v git >/dev/null 2>&1; then \
		echo "✅ Git available"; \
	else \
		echo "❌ Git not found"; \
	fi
	@echo "Python packages:"
	@$(PIP) list | grep -E "(pandas|numpy|scikit-learn|opencv|plotly)" || echo "Core packages not installed"

# Show project status
status:
	@echo "RallyScope Project Status"
	@echo "========================"
	@echo "Data files:"
	@ls -la $(DATA_DIR)/ 2>/dev/null || echo "  No data directory"
	@echo "Models:"
	@ls -la $(MODELS_DIR)/ 2>/dev/null || echo "  No models directory"
	@echo "Website:"
	@ls -la $(SITE_DIR)/ 2>/dev/null || echo "  No site directory"
	@echo "Cache size:"
	@du -sh $(DATA_DIR)/interim/ 2>/dev/null || echo "  No cache"

# Create project archive
archive:
	@echo "Creating project archive..."
	tar -czf rallyscope-$(shell date +%Y%m%d).tar.gz \
		--exclude='$(DATA_DIR)/raw' \
		--exclude='$(DATA_DIR)/interim' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		.
	@echo "✅ Archive created: rallyscope-$(shell date +%Y%m%d).tar.gz"