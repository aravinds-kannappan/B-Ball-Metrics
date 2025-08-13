/**
 * RallyScope - Tennis Intelligence & Vision
 * Main JavaScript functionality
 */

// Global configuration
const RALLYSCOPE = {
    version: '1.0.0',
    apiEndpoint: null, // Static site - no API
    chartDefaults: {
        responsive: true,
        displayModeBar: false,
        margin: { t: 40, b: 40, l: 60, r: 20 }
    }
};

// Utility functions
const Utils = {
    /**
     * Format numbers with appropriate precision
     */
    formatNumber: (num, decimals = 2) => {
        if (typeof num !== 'number') return 'N/A';
        return num.toFixed(decimals);
    },

    /**
     * Format percentages
     */
    formatPercentage: (num, decimals = 1) => {
        if (typeof num !== 'number') return 'N/A';
        return (num * 100).toFixed(decimals) + '%';
    },

    /**
     * Debounce function for search inputs
     */
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Get color for archetype
     */
    getArchetypeColor: (archetype) => {
        const colors = {
            'serve-cannon': '#FF6B6B',
            'aggressive-returner': '#4ECDC4',
            'clay-court-specialist': '#45B7D1',
            'all-court-elite': '#96CEB4',
            'developing-player': '#FECA57',
            'baseline-grinder': '#A0A0A0',
            'unique-style': '#DDA0DD'
        };
        
        const key = archetype.toLowerCase().replace(/\s+/g, '-');
        return colors[key] || '#2E86AB';
    },

    /**
     * Generate sparkline SVG
     */
    generateSparkline: (data, width = 100, height = 30) => {
        if (!data || data.length === 0) return '';
        
        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min || 1;
        
        const points = data.map((value, index) => {
            const x = (index / (data.length - 1)) * width;
            const y = height - ((value - min) / range) * height;
            return `${x},${y}`;
        }).join(' ');
        
        return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
                    <polyline points="${points}" fill="none" stroke="#2E86AB" stroke-width="2"/>
                </svg>`;
    }
};

// Chart rendering utilities
const ChartUtils = {
    /**
     * Default Plotly configuration
     */
    getDefaultConfig: () => ({
        responsive: true,
        displayModeBar: false,
        ...RALLYSCOPE.chartDefaults
    }),

    /**
     * Create bar chart
     */
    createBarChart: (element, data, layout = {}) => {
        const defaultLayout = {
            margin: RALLYSCOPE.chartDefaults.margin,
            ...layout
        };
        
        Plotly.newPlot(element, data, defaultLayout, ChartUtils.getDefaultConfig());
    },

    /**
     * Create scatter plot
     */
    createScatterPlot: (element, data, layout = {}) => {
        const defaultLayout = {
            margin: RALLYSCOPE.chartDefaults.margin,
            ...layout
        };
        
        Plotly.newPlot(element, data, defaultLayout, ChartUtils.getDefaultConfig());
    },

    /**
     * Create line chart
     */
    createLineChart: (element, data, layout = {}) => {
        const defaultLayout = {
            margin: RALLYSCOPE.chartDefaults.margin,
            ...layout
        };
        
        Plotly.newPlot(element, data, defaultLayout, ChartUtils.getDefaultConfig());
    },

    /**
     * Resize all charts (useful for responsive design)
     */
    resizeAllCharts: () => {
        const charts = document.querySelectorAll('[id*="chart"], [id*="plot"]');
        charts.forEach(chart => {
            if (chart._fullLayout) {
                Plotly.Plots.resize(chart);
            }
        });
    }
};

// Data loading utilities
const DataLoader = {
    /**
     * Load JSON data from assets
     */
    loadJSON: async (filename) => {
        try {
            const response = await fetch(`assets/data/${filename}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`Error loading ${filename}:`, error);
            return null;
        }
    },

    /**
     * Load player profiles
     */
    loadPlayerProfiles: () => DataLoader.loadJSON('player_archetypes.json'),

    /**
     * Load model results
     */
    loadModelResults: () => DataLoader.loadJSON('outcome_model.json'),

    /**
     * Load vision analysis
     */
    loadVisionAnalysis: () => DataLoader.loadJSON('vision_analysis.json'),

    /**
     * Load match momentum data
     */
    loadMatchMomentum: (matchId) => DataLoader.loadJSON(`../matches/${matchId}_momentum.json`)
};

// Search and filtering
const SearchFilter = {
    /**
     * Initialize search functionality
     */
    init: (searchInputId, tableBodyId, filterCallback) => {
        const searchInput = document.getElementById(searchInputId);
        if (!searchInput) return;

        const debouncedFilter = Utils.debounce(() => {
            const query = searchInput.value.toLowerCase().trim();
            SearchFilter.filterTable(tableBodyId, query, filterCallback);
        }, 300);

        searchInput.addEventListener('input', debouncedFilter);
    },

    /**
     * Filter table rows
     */
    filterTable: (tableBodyId, query, customFilter) => {
        const tableBody = document.getElementById(tableBodyId);
        if (!tableBody) return;

        const rows = Array.from(tableBody.querySelectorAll('tr'));
        let visibleCount = 0;

        rows.forEach(row => {
            const isVisible = customFilter ? customFilter(row, query) : 
                             SearchFilter.defaultFilter(row, query);
            
            row.style.display = isVisible ? '' : 'none';
            if (isVisible) visibleCount++;
        });

        // Update count display
        const countElement = document.getElementById('table-info');
        if (countElement) {
            countElement.textContent = `Showing ${visibleCount} of ${rows.length} items`;
        }
    },

    /**
     * Default filter function
     */
    defaultFilter: (row, query) => {
        if (!query) return true;
        const text = row.textContent.toLowerCase();
        return text.includes(query);
    }
};

// Modal management
const ModalManager = {
    /**
     * Initialize modal functionality
     */
    init: (modalId) => {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        const closeBtn = modal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => ModalManager.hide(modalId));
        }

        // Close on backdrop click
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                ModalManager.hide(modalId);
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && ModalManager.isVisible(modalId)) {
                ModalManager.hide(modalId);
            }
        });
    },

    /**
     * Show modal
     */
    show: (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    },

    /**
     * Hide modal
     */
    hide: (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    },

    /**
     * Check if modal is visible
     */
    isVisible: (modalId) => {
        const modal = document.getElementById(modalId);
        return modal && modal.style.display === 'block';
    }
};

// Performance monitoring
const Performance = {
    /**
     * Track page load time
     */
    trackPageLoad: () => {
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            console.log(`Page loaded in ${Math.round(loadTime)}ms`);
            
            // Optional: Send to analytics
            Performance.reportMetric('page_load_time', loadTime);
        });
    },

    /**
     * Track chart render time
     */
    trackChartRender: (chartId, startTime) => {
        const endTime = performance.now();
        const renderTime = endTime - startTime;
        console.log(`Chart ${chartId} rendered in ${Math.round(renderTime)}ms`);
        
        Performance.reportMetric('chart_render_time', renderTime, { chart_id: chartId });
    },

    /**
     * Report metric (stub for analytics integration)
     */
    reportMetric: (metric, value, metadata = {}) => {
        // In a real implementation, this would send to analytics service
        console.debug(`Metric: ${metric} = ${value}`, metadata);
    }
};

// Error handling
const ErrorHandler = {
    /**
     * Global error handler
     */
    init: () => {
        window.addEventListener('error', ErrorHandler.handleError);
        window.addEventListener('unhandledrejection', ErrorHandler.handlePromiseRejection);
    },

    /**
     * Handle JavaScript errors
     */
    handleError: (event) => {
        console.error('JavaScript error:', event.error);
        ErrorHandler.reportError(event.error);
    },

    /**
     * Handle promise rejections
     */
    handlePromiseRejection: (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        ErrorHandler.reportError(event.reason);
    },

    /**
     * Report error (stub)
     */
    reportError: (error) => {
        // In a real implementation, this would send to error tracking service
        console.debug('Error reported:', error);
    },

    /**
     * Show user-friendly error message
     */
    showErrorMessage: (message, container = null) => {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <p><strong>Oops!</strong> ${message}</p>
            <p>Please refresh the page or try again later.</p>
        `;
        
        if (container) {
            container.innerHTML = '';
            container.appendChild(errorDiv);
        } else {
            document.body.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);
        }
    }
};

// Theme management
const ThemeManager = {
    /**
     * Initialize theme system
     */
    init: () => {
        const savedTheme = localStorage.getItem('rallyscope-theme') || 'light';
        ThemeManager.setTheme(savedTheme);
    },

    /**
     * Set theme
     */
    setTheme: (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('rallyscope-theme', theme);
    },

    /**
     * Toggle theme
     */
    toggleTheme: () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        ThemeManager.setTheme(newTheme);
    }
};

// Main application initialization
const RallyScope = {
    /**
     * Initialize the application
     */
    init: () => {
        console.log(`RallyScope v${RALLYSCOPE.version} initializing...`);
        
        // Initialize core systems
        ErrorHandler.init();
        Performance.trackPageLoad();
        ThemeManager.init();
        
        // Initialize page-specific functionality
        const page = RallyScope.getCurrentPage();
        console.log(`Current page: ${page}`);
        
        switch (page) {
            case 'index':
                RallyScope.initDashboard();
                break;
            case 'players':
                RallyScope.initPlayersPage();
                break;
            case 'matches':
                RallyScope.initMatchesPage();
                break;
            case 'vision':
                RallyScope.initVisionPage();
                break;
        }
        
        // Global event listeners
        RallyScope.initGlobalEvents();
        
        console.log('RallyScope initialization complete');
    },

    /**
     * Get current page from URL
     */
    getCurrentPage: () => {
        const path = window.location.pathname;
        const filename = path.split('/').pop() || 'index.html';
        return filename.replace('.html', '');
    },

    /**
     * Initialize dashboard page
     */
    initDashboard: () => {
        console.log('Initializing dashboard...');
        // Dashboard-specific initialization is handled in the template
    },

    /**
     * Initialize players page
     */
    initPlayersPage: () => {
        console.log('Initializing players page...');
        
        // Initialize search
        SearchFilter.init('player-search', 'players-table-body', (row, query) => {
            const playerId = row.cells[0]?.textContent?.toLowerCase() || '';
            const archetype = row.getAttribute('data-archetype')?.toLowerCase() || '';
            return playerId.includes(query) || archetype.includes(query);
        });
        
        // Initialize modal
        ModalManager.init('player-modal');
    },

    /**
     * Initialize matches page
     */
    initMatchesPage: () => {
        console.log('Initializing matches page...');
        ModalManager.init('match-modal');
    },

    /**
     * Initialize vision page
     */
    initVisionPage: () => {
        console.log('Initializing vision page...');
        ModalManager.init('serve-modal');
    },

    /**
     * Initialize global event listeners
     */
    initGlobalEvents: () => {
        // Responsive chart resizing
        window.addEventListener('resize', Utils.debounce(() => {
            ChartUtils.resizeAllCharts();
        }, 250));
        
        // Navigation highlighting
        RallyScope.highlightCurrentNavigation();
    },

    /**
     * Highlight current navigation item
     */
    highlightCurrentNavigation: () => {
        const currentPage = RallyScope.getCurrentPage();
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            const linkPage = href ? href.replace('.html', '') : '';
            
            if (linkPage === currentPage || (currentPage === 'index' && href === 'index.html')) {
                link.style.color = '#F18F01';
                link.style.fontWeight = '600';
            }
        });
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', RallyScope.init);

// Export for global access
window.RallyScope = RallyScope;
window.Utils = Utils;
window.ChartUtils = ChartUtils;
window.DataLoader = DataLoader;
window.SearchFilter = SearchFilter;
window.ModalManager = ModalManager;