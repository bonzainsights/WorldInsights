/**
 * WorldInsights API Client
 * 
 * A lightweight, dependency-free API client for interacting with the WorldInsights backend.
 * Provides caching, debouncing, and error handling out of the box.
 * 
 * @example
 * // Fetch all countries
 * const countries = await WorldInsightsAPI.getCountries();
 * 
 * // Fetch indicators by source
 * const indicators = await WorldInsightsAPI.getIndicators('worldbank');
 * 
 * // Fetch data for plotting
 * const data = await WorldInsightsAPI.getData(['USA', 'GBR'], ['NY.GDP.MKTP.CD'], [2015, 2020]);
 */

(function(global) {
  'use strict';

  // Configuration
  const CONFIG = {
    BASE_URL: '',  // Relative URLs for same-origin
    CACHE_TTL: 5 * 60 * 1000,  // 5 minutes cache TTL
    DEBOUNCE_DELAY: 300,  // 300ms debounce for search inputs
    TIMEOUT: 30000,  // 30 second timeout
  };

  // In-memory cache
  const cache = new Map();

  /**
   * Cache utilities
   */
  const Cache = {
    /**
     * Get cached data if not expired
     * @param {string} key - Cache key
     * @returns {*} Cached data or null
     */
    get(key) {
      const item = cache.get(key);
      if (!item) return null;
      
      const { data, timestamp } = item;
      const now = Date.now();
      
      if (now - timestamp > CONFIG.CACHE_TTL) {
        cache.delete(key);
        return null;
      }
      
      return data;
    },

    /**
     * Set cache data
     * @param {string} key - Cache key
     * @param {*} data - Data to cache
     */
    set(key, data) {
      cache.set(key, {
        data,
        timestamp: Date.now()
      });
    },

    /**
     * Clear all cache
     */
    clear() {
      cache.clear();
    },

    /**
     * Clear expired entries
     */
    cleanup() {
      const now = Date.now();
      for (const [key, item] of cache.entries()) {
        if (now - item.timestamp > CONFIG.CACHE_TTL) {
          cache.delete(key);
        }
      }
    }
  };

  /**
   * Debounce utility
   * @param {Function} func - Function to debounce
   * @param {number} wait - Wait time in ms
   * @returns {Function} Debounced function
   */
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Toast notification utilities
   */
  const Toast = {
    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in ms
     */
    show(message, type = 'info', duration = 5000) {
      const container = document.getElementById('toast-container');
      if (!container) {
        console.warn('Toast container not found');
        return;
      }

      const toast = document.createElement('div');
      toast.className = `toast flex items-center p-4 rounded-lg shadow-lg max-w-sm card-hover ${this.getTypeClasses(type)}`;
      toast.setAttribute('role', 'alert');
      
      toast.innerHTML = `
        ${this.getIcon(type)}
        <p class="text-sm font-medium ml-3">${this.escapeHtml(message)}</p>
        <button onclick="this.parentElement.remove()" class="ml-auto -mx-1.5 -my-1.5 rounded-lg p-1.5 inline-flex h-8 w-8 hover:bg-gray-200 transition-colors" aria-label="Dismiss">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      `;

      container.appendChild(toast);

      // Trigger animation
      requestAnimationFrame(() => {
        toast.classList.add('show');
      });

      // Auto-remove
      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
      }, duration);
    },

    /**
     * Get CSS classes for toast type
     */
    getTypeClasses(type) {
      const classes = {
        success: 'bg-green-50 border-l-4 border-green-500 text-green-800',
        error: 'bg-red-50 border-l-4 border-red-500 text-red-800',
        warning: 'bg-yellow-50 border-l-4 border-yellow-500 text-yellow-800',
        info: 'bg-blue-50 border-l-4 border-blue-500 text-blue-800'
      };
      return classes[type] || classes.info;
    },

    /**
     * Get icon for toast type
     */
    getIcon(type) {
      const icons = {
        success: '<svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        error: '<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        warning: '<svg class="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
        info: '<svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
      };
      return icons[type] || icons.info;
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
  };

  /**
   * HTTP request utilities
   */
  const HTTP = {
    /**
     * Make a fetch request with timeout and error handling
     * @param {string} url - Request URL
     * @param {Object} options - Fetch options
     * @returns {Promise<*>} Response data
     */
    async request(url, options = {}) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), CONFIG.TIMEOUT);

      try {
        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          }
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Request failed' }));
          throw new Error(error.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
          throw new Error('Request timeout');
        }
        
        throw error;
      }
    },

    /**
     * GET request
     */
    async get(url, params = {}) {
      const queryString = new URLSearchParams(params).toString();
      const fullUrl = queryString ? `${url}?${queryString}` : url;
      return this.request(fullUrl);
    },

    /**
     * POST request
     */
    async post(url, data = {}) {
      return this.request(url, {
        method: 'POST',
        body: JSON.stringify(data)
      });
    }
  };

  /**
   * Main API Client
   */
  const WorldInsightsAPI = {
    /**
     * Get all available countries
     * @returns {Promise<Array>} List of countries
     */
    async getCountries() {
      const cacheKey = 'api:countries';
      const cached = Cache.get(cacheKey);
      
      if (cached) {
        console.log('[API] Countries from cache');
        return cached;
      }

      try {
        const response = await HTTP.get('/api/plot/countries');
        const countries = response.countries || [];
        Cache.set(cacheKey, countries);
        console.log(`[API] Fetched ${countries.length} countries`);
        return countries;
      } catch (error) {
        console.error('[API] Error fetching countries:', error);
        Toast.show('Failed to load countries', 'error');
        return [];
      }
    },

    /**
     * Get indicators by source and category
     * @param {string} source - Data source (worldbank, who, fao, nasa, openmeteo)
     * @param {string} category - Optional category filter
     * @returns {Promise<Array>} List of indicators
     */
    async getIndicators(source = null, category = null) {
      const cacheKey = `api:indicators:${source}:${category}`;
      const cached = Cache.get(cacheKey);
      
      if (cached) {
        console.log('[API] Indicators from cache');
        return cached;
      }

      try {
        const response = await HTTP.get('/api/plot/indicators');
        let indicators = response.indicators || [];

        // Filter by source if specified
        if (source) {
          indicators = indicators.filter(ind => ind.source === source);
        }

        // Filter by category if specified (based on indicator code patterns)
        if (category) {
          indicators = indicators.filter(ind => 
            ind.code?.includes(category) || ind.name?.toLowerCase().includes(category.toLowerCase())
          );
        }

        Cache.set(cacheKey, indicators);
        console.log(`[API] Fetched ${indicators.length} indicators`);
        return indicators;
      } catch (error) {
        console.error('[API] Error fetching indicators:', error);
        Toast.show('Failed to load indicators', 'error');
        return [];
      }
    },

    /**
     * Get plot data for specified countries, indicators, and years
     * @param {Array<string>} countries - Country codes
     * @param {Array<string>} indicators - Indicator codes
     * @param {Array<number>} years - Year range [start, end]
     * @param {string} chartType - Chart type for transformation
     * @returns {Promise<Object>} Plot data
     */
    async getData(countries, indicators, years = null, chartType = 'line') {
      if (!countries || countries.length === 0) {
        throw new Error('At least one country is required');
      }
      if (!indicators || indicators.length === 0) {
        throw new Error('At least one indicator is required');
      }

      const params = {
        countries: countries.join(','),
        indicators: indicators.join(','),
        chart_type: chartType
      };

      if (years && years.length === 2) {
        params.start_year = years[0];
        params.end_year = years[1];
      }

      try {
        const response = await HTTP.get('/api/plot/data', params);
        
        if (response.warning) {
          console.warn('[API] Partial data:', response.warning);
          Toast.show(response.warning, 'warning', 8000);
        }

        console.log(`[API] Fetched ${response.count || 0} data points`);
        return response;
      } catch (error) {
        console.error('[API] Error fetching data:', error);
        Toast.show(error.message || 'Failed to load data', 'error');
        throw error;
      }
    },

    /**
     * Get availability matrix for countries and indicators
     * @param {Array<string>} countries - Country codes
     * @param {Array<string>} indicators - Indicator codes
     * @returns {Promise<Object>} Availability matrix
     */
    async getAvailability(countries, indicators) {
      // This uses the existing data endpoint to check availability
      // A more efficient implementation would have a dedicated availability endpoint
      try {
        const response = await HTTP.get('/api/plot/data', {
          countries: countries.join(','),
          indicators: indicators.join(',')
        });

        // Analyze the data to determine availability
        const availability = {};
        const data = response.data || [];

        for (const country of countries) {
          availability[country] = {};
          for (const indicator of indicators) {
            const hasData = data.some(d => 
              d.country === country && d.indicator === indicator
            );
            availability[country][indicator] = hasData;
          }
        }

        return { availability, data };
      } catch (error) {
        console.error('[API] Error checking availability:', error);
        return { availability: {}, data: [], error: error.message };
      }
    },

    /**
     * Get globe data for 3D visualization
     * @param {string} source - Data source
     * @param {string} indicator - Indicator code
     * @param {number} year - Year
     * @returns {Promise<Object>} GeoJSON data
     */
    async getGlobeData(source, indicator, year) {
      try {
        const response = await HTTP.get('/api/data/globe', {
          source,
          indicator,
          year
        });
        console.log(`[API] Fetched globe data for ${indicator} (${year})`);
        return response;
      } catch (error) {
        console.error('[API] Error fetching globe data:', error);
        Toast.show('Failed to load globe data', 'error');
        throw error;
      }
    },

    /**
     * Calculate correlations between indicators
     * @param {Array<string>} countries - Country codes
     * @param {Array<string>} indicators - Indicator codes
     * @param {Array<number>} years - Year range
     * @returns {Promise<Object>} Correlation matrix
     */
    async getCorrelations(countries, indicators, years = null) {
      const params = {
        countries: countries.join(','),
        indicators: indicators.join(',')
      };

      if (years && years.length === 2) {
        params.start_year = years[0];
        params.end_year = years[1];
      }

      try {
        const response = await HTTP.get('/api/plot/correlations', params);
        console.log('[API] Calculated correlations');
        return response.correlations || {};
      } catch (error) {
        console.error('[API] Error calculating correlations:', error);
        Toast.show('Failed to calculate correlations', 'error');
        throw error;
      }
    },

    /**
     * Save dashboard configuration
     * @param {Object} config - Dashboard configuration
     * @returns {Promise<Object>} Saved dashboard
     */
    async saveDashboard(config) {
      // For now, save to localStorage
      // In production, this would POST to a backend endpoint
      try {
        const dashboards = this.getSavedDashboards();
        const id = 'dashboard_' + Date.now();
        
        dashboards.push({
          id,
          name: config.name || 'Untitled Dashboard',
          config,
          createdAt: new Date().toISOString()
        });

        localStorage.setItem('worldinsights_dashboards', JSON.stringify(dashboards));
        console.log('[API] Dashboard saved to localStorage');
        Toast.show('Dashboard saved', 'success');
        
        return { id, ...dashboards[dashboards.length - 1] };
      } catch (error) {
        console.error('[API] Error saving dashboard:', error);
        Toast.show('Failed to save dashboard', 'error');
        throw error;
      }
    },

    /**
     * Load dashboard by ID
     * @param {string} id - Dashboard ID
     * @returns {Object|null} Dashboard configuration
     */
    loadDashboard(id) {
      const dashboards = this.getSavedDashboards();
      const dashboard = dashboards.find(d => d.id === id);
      
      if (!dashboard) {
        Toast.show('Dashboard not found', 'error');
        return null;
      }

      console.log('[API] Dashboard loaded:', dashboard.name);
      return dashboard;
    },

    /**
     * Get all saved dashboards
     * @returns {Array} List of saved dashboards
     */
    getSavedDashboards() {
      try {
        const data = localStorage.getItem('worldinsights_dashboards');
        return data ? JSON.parse(data) : [];
      } catch (error) {
        console.error('[API] Error loading dashboards:', error);
        return [];
      }
    },

    /**
     * Delete dashboard
     * @param {string} id - Dashboard ID
     * @returns {boolean} Success
     */
    deleteDashboard(id) {
      try {
        const dashboards = this.getSavedDashboards();
        const filtered = dashboards.filter(d => d.id !== id);
        localStorage.setItem('worldinsights_dashboards', JSON.stringify(filtered));
        Toast.show('Dashboard deleted', 'success');
        return true;
      } catch (error) {
        console.error('[API] Error deleting dashboard:', error);
        Toast.show('Failed to delete dashboard', 'error');
        return false;
      }
    },

    /**
     * Search indicators
     * @param {string} query - Search query
     * @param {string} source - Optional source filter
     * @returns {Promise<Array>} Matching indicators
     */
    async searchIndicators(query, source = null) {
      if (!query || query.trim().length < 2) {
        return [];
      }

      const indicators = await this.getIndicators(source);
      const searchTerm = query.toLowerCase();

      return indicators.filter(ind => 
        ind.name?.toLowerCase().includes(searchTerm) ||
        ind.code?.toLowerCase().includes(searchTerm) ||
        ind.description?.toLowerCase().includes(searchTerm)
      );
    },

    /**
     * Search countries
     * @param {string} query - Search query
     * @returns {Promise<Array>} Matching countries
     */
    async searchCountries(query) {
      if (!query || query.trim().length < 2) {
        return [];
      }

      const countries = await this.getCountries();
      const searchTerm = query.toLowerCase();

      return countries.filter(country => 
        country.name?.toLowerCase().includes(searchTerm) ||
        country.code?.toLowerCase().includes(searchTerm)
      );
    },

    /**
     * Clear API cache
     */
    clearCache() {
      Cache.clear();
      console.log('[API] Cache cleared');
      Toast.show('Cache cleared', 'info');
    },

    /**
     * Get cache statistics
     * @returns {Object} Cache stats
     */
    getCacheStats() {
      return {
        size: cache.size,
        keys: Array.from(cache.keys())
      };
    }
  };

  // Export to global scope
  global.WorldInsightsAPI = WorldInsightsAPI;
  global.WorldInsightsCache = Cache;
  global.WorldInsightsToast = Toast;
  global.debounce = debounce;

  // Auto-cleanup cache every 10 minutes
  setInterval(() => Cache.cleanup(), 10 * 60 * 1000);

  // Log initialization
  console.log('[WorldInsights API] Initialized');

})(typeof window !== 'undefined' ? window : this);
