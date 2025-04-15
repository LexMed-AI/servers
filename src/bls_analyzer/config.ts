/**
 * Base URLs for different BLS services
 */
export const URLS = {
  DOT_SOC_CROSSWALK: 'https://www.onetonline.org/crosswalk/DOT',
  OEWS_DATA: 'https://www.bls.gov/oes/current/oes_nat.htm',
  NAICS_SEARCH: 'https://www.naics.com/search',
} as const

/**
 * Puppeteer configuration
 */
export const PUPPETEER_CONFIG = {
  headless: 'new' as const,
  defaultViewport: {
    width: 1920,
    height: 1080,
  },
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--disable-gpu',
    '--window-size=1920,1080',
  ],
} as const

/**
 * Cache configuration
 */
export const CACHE_CONFIG = {
  DOT_SOC_TTL: 30 * 24 * 60 * 60 * 1000, // 30 days
  OEWS_DATA_TTL: 7 * 24 * 60 * 60 * 1000, // 7 days
  NAICS_TTL: 30 * 24 * 60 * 60 * 1000,    // 30 days
} as const

/**
 * Request configuration
 */
export const REQUEST_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000,
  minRandomDelay: 500,
  maxRandomDelay: 2000,
} as const

/**
 * Selectors for web scraping
 */
export const SELECTORS = {
  DOT_SOC: {
    searchInput: '#code',
    submitButton: 'input[type="submit"]',
    resultsTable: 'table.display',
    socCodeCell: 'td:nth-child(1)',
    occupationTitleCell: 'td:nth-child(2)',
  },
  OEWS: {
    occupationTable: '#national table',
    dataRow: 'tr[data-code]',
    socCodeAttr: 'data-code',
    employmentCell: 'td:nth-child(2)',
    meanWageCell: 'td:nth-child(3)',
    medianWageCell: 'td:nth-child(4)',
  },
  NAICS: {
    searchInput: '#search-input',
    searchButton: '#search-button',
    resultsContainer: '.search-results',
    codeElement: '.naics-code',
    titleElement: '.naics-title',
    descriptionElement: '.naics-description',
  },
} as const

/**
 * Error messages
 */
export const ERROR_MESSAGES = {
  BROWSER_INIT: 'Failed to initialize Puppeteer browser',
  INVALID_DOT: 'Invalid DOT code format',
  INVALID_SOC: 'Invalid SOC code format',
  INVALID_NAICS: 'Invalid NAICS code format',
  SCRAPING_FAILED: 'Failed to scrape data',
  NO_RESULTS: 'No results found',
  CACHE_ERROR: 'Failed to access cache',
} as const

/**
 * Screenshot configuration
 */
export const SCREENSHOT_CONFIG = {
  type: 'png' as const,
  fullPage: true,
  quality: 80,
} as const 