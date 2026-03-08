/**
 * WorldInsights Main JavaScript
 * 
 * Core utilities and initialization for the WorldInsights frontend.
 */

(function() {
  'use strict';

  /**
   * Initialize on DOM ready
   */
  document.addEventListener('DOMContentLoaded', function() {
    console.log('[WorldInsights] Application initialized');
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize smooth scroll
    initSmoothScroll();
    
    // Initialize lazy loading
    initLazyLoading();
    
    // Initialize form enhancements
    initFormEnhancements();
  });

  /**
   * Initialize tooltips (using title attribute)
   */
  function initTooltips() {
    // Simple tooltip implementation using Alpine.js or native
    document.querySelectorAll('[data-tooltip]').forEach(el => {
      el.addEventListener('mouseenter', showTooltip);
      el.addEventListener('mouseleave', hideTooltip);
    });
  }

  function showTooltip(e) {
    const tooltip = e.target.getAttribute('data-tooltip');
    if (!tooltip) return;

    const tooltipEl = document.createElement('div');
    tooltipEl.className = 'fixed z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg pointer-events-none';
    tooltipEl.textContent = tooltip;
    tooltipEl.id = 'active-tooltip';
    
    document.body.appendChild(tooltipEl);
    
    const rect = e.target.getBoundingClientRect();
    tooltipEl.style.top = rect.top - tooltipEl.offsetHeight - 8 + 'px';
    tooltipEl.style.left = rect.left + (rect.width - tooltipEl.offsetWidth) / 2 + 'px';
  }

  function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) tooltip.remove();
  }

  /**
   * Initialize smooth scroll for anchor links
   */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href === '#') return;
        
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  /**
   * Initialize lazy loading for images
   */
  function initLazyLoading() {
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
            }
            observer.unobserve(img);
          }
        });
      });

      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }
  }

  /**
   * Initialize form enhancements
   */
  function initFormEnhancements() {
    // Auto-resize textareas
    document.querySelectorAll('textarea[data-autoresize]').forEach(textarea => {
      textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
      });
    });

    // Confirm before destructive actions
    document.querySelectorAll('[data-confirm]').forEach(el => {
      el.addEventListener('click', function(e) {
        const message = this.getAttribute('data-confirm');
        if (!confirm(message)) {
          e.preventDefault();
          e.stopPropagation();
        }
      });
    });
  }

  /**
   * Format numbers with commas
   * @param {number} num - Number to format
   * @returns {string} Formatted number
   */
  function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return new Intl.NumberFormat().format(num);
  }

  /**
   * Format large numbers with K, M, B suffixes
   * @param {number} num - Number to format
   * @returns {string} Formatted number
   */
  function formatCompactNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      notation: 'compact',
      maximumFractionDigits: 1
    }).format(num);
  }

  /**
   * Format year range
   * @param {number} start - Start year
   * @param {number} end - End year
   * @returns {string} Formatted year range
   */
  function formatYearRange(start, end) {
    if (!start && !end) return 'All years';
    if (start && !end) return `${start} - Present`;
    if (!start && end) return `Until ${end}`;
    return `${start} - ${end}`;
  }

  /**
   * Debounce function
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
   * Throttle function
   * @param {Function} func - Function to throttle
   * @param {number} limit - Time limit in ms
   * @returns {Function} Throttled function
   */
  function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  /**
   * Copy text to clipboard
   * @param {string} text - Text to copy
   * @returns {Promise<boolean>} Success
   */
  async function copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      if (window.WorldInsightsToast) {
        window.WorldInsightsToast.show('Copied to clipboard', 'success');
      }
      return true;
    } catch (err) {
      console.error('Failed to copy:', err);
      if (window.WorldInsightsToast) {
        window.WorldInsightsToast.show('Failed to copy', 'error');
      }
      return false;
    }
  }

  /**
   * Download data as JSON file
   * @param {Object} data - Data to download
   * @param {string} filename - Filename
   */
  function downloadJSON(data, filename = 'data.json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    if (window.WorldInsightsToast) {
      window.WorldInsightsToast.show('Download started', 'success');
    }
  }

  /**
   * Download data as CSV file
   * @param {Array} data - Array of objects
   * @param {string} filename - Filename
   */
  function downloadCSV(data, filename = 'data.csv') {
    if (!data || data.length === 0) {
      if (window.WorldInsightsToast) {
        window.WorldInsightsToast.show('No data to export', 'warning');
      }
      return;
    }

    const headers = Object.keys(data[0]);
    const csv = [
      headers.join(','),
      ...data.map(row => headers.map(h => JSON.stringify(row[h])).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    if (window.WorldInsightsToast) {
      window.WorldInsightsToast.show('Download started', 'success');
    }
  }

  // Export utilities to global scope
  window.WorldInsightsUtils = {
    formatNumber,
    formatCompactNumber,
    formatYearRange,
    debounce,
    throttle,
    copyToClipboard,
    downloadJSON,
    downloadCSV
  };

})();
