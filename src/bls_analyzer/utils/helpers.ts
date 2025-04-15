/**
 * Delays execution for specified milliseconds
 */
export const delay = (ms: number): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms))

/**
 * Sanitizes input for use in filenames and cache keys
 */
export const sanitizeInput = (input: string): string => {
  return input
    .replace(/[^a-zA-Z0-9-_]/g, '_') // Replace invalid chars with underscore
    .replace(/_+/g, '_')             // Replace multiple underscores with single
    .toLowerCase()
}

/**
 * Extracts numeric value from string, handling various formats
 */
export const extractNumber = (text: string): number | null => {
  const match = text.replace(/,/g, '').match(/-?\d+\.?\d*/)
  return match ? parseFloat(match[0]) : null
}

/**
 * Formats currency value to number
 */
export const parseCurrency = (value: string): number | null => {
  const cleaned = value.replace(/[^0-9.-]/g, '')
  const number = parseFloat(cleaned)
  return isNaN(number) ? null : number
}

/**
 * Validates DOT code format
 */
export const isValidDOTCode = (code: string): boolean => {
  return /^\d{3}\.\d{3}-\d{3}$/.test(code)
}

/**
 * Validates SOC code format
 */
export const isValidSOCCode = (code: string): boolean => {
  return /^\d{2}-\d{4}$/.test(code)
}

/**
 * Validates NAICS code format
 */
export const isValidNAICSCode = (code: string): boolean => {
  return /^\d{2,6}$/.test(code)
}

/**
 * Retries an async function with exponential backoff
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxAttempts = 3,
  baseDelay = 1000
): Promise<T> {
  let lastError: Error | null = null
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      if (attempt === maxAttempts) break
      
      const delayMs = baseDelay * Math.pow(2, attempt - 1)
      await delay(delayMs)
    }
  }
  
  throw lastError
}

/**
 * Chunks an array into smaller arrays of specified size
 */
export function chunk<T>(array: T[], size: number): T[][] {
  return Array.from({ length: Math.ceil(array.length / size) }, (_, i) =>
    array.slice(i * size, i * size + size)
  )
}

/**
 * Generates a random delay between min and max milliseconds
 */
export const randomDelay = (min: number, max: number): Promise<void> => {
  const delay = Math.floor(Math.random() * (max - min + 1) + min)
  return new Promise(resolve => setTimeout(resolve, delay))
}

/**
 * Formats a date as an ISO string without milliseconds
 */
export const formatDate = (date: Date = new Date()): string => {
  return date.toISOString().split('.')[0] + 'Z'
} 