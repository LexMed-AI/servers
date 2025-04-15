import fs from 'fs/promises'
import path from 'path'
import { sanitizeInput, formatDate } from './helpers.js'
import { ERROR_MESSAGES } from '../../../../bls_analyzer/config.js'

interface CacheEntry<T> {
  data: T
  timestamp: string
  expiresAt: string
}

export class CacheManager {
  private cacheDir: string

  constructor(cacheDir: string) {
    this.cacheDir = cacheDir
  }

  /**
   * Initialize the cache directory
   */
  async init(): Promise<void> {
    try {
      await fs.mkdir(this.cacheDir, { recursive: true })
    } catch (error) {
      throw new Error(`Failed to initialize cache directory: ${error.message}`)
    }
  }

  /**
   * Get the full path for a cache key
   */
  private getCachePath(key: string): string {
    const sanitizedKey = sanitizeInput(key)
    return path.join(this.cacheDir, `${sanitizedKey}.json`)
  }

  /**
   * Check if a cache entry exists and is valid
   */
  private async isValidCache(filePath: string, ttl: number): Promise<boolean> {
    try {
      const stats = await fs.stat(filePath)
      const now = new Date()
      const fileAge = now.getTime() - stats.mtime.getTime()
      return fileAge < ttl
    } catch (error) {
      return false
    }
  }

  /**
   * Get data from cache
   */
  async get<T>(key: string, ttl: number): Promise<T | null> {
    const filePath = this.getCachePath(key)
    
    try {
      if (!(await this.isValidCache(filePath, ttl))) {
        return null
      }

      const data = await fs.readFile(filePath, 'utf-8')
      const cacheEntry: CacheEntry<T> = JSON.parse(data)
      return cacheEntry.data
    } catch (error) {
      if (error.code === 'ENOENT') {
        return null
      }
      throw new Error(`${ERROR_MESSAGES.CACHE_ERROR}: ${error.message}`)
    }
  }

  /**
   * Set data in cache
   */
  async set<T>(key: string, data: T, ttl: number): Promise<void> {
    const filePath = this.getCachePath(key)
    const now = new Date()
    const expiresAt = new Date(now.getTime() + ttl)

    const cacheEntry: CacheEntry<T> = {
      data,
      timestamp: formatDate(now),
      expiresAt: formatDate(expiresAt)
    }

    try {
      await fs.writeFile(filePath, JSON.stringify(cacheEntry, null, 2), 'utf-8')
    } catch (error) {
      throw new Error(`${ERROR_MESSAGES.CACHE_ERROR}: ${error.message}`)
    }
  }

  /**
   * Delete a cache entry
   */
  async delete(key: string): Promise<void> {
    const filePath = this.getCachePath(key)
    try {
      await fs.unlink(filePath)
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw new Error(`${ERROR_MESSAGES.CACHE_ERROR}: ${error.message}`)
      }
    }
  }

  /**
   * Clear all cache entries
   */
  async clear(): Promise<void> {
    try {
      const files = await fs.readdir(this.cacheDir)
      await Promise.all(
        files.map(file => fs.unlink(path.join(this.cacheDir, file)))
      )
    } catch (error) {
      throw new Error(`${ERROR_MESSAGES.CACHE_ERROR}: ${error.message}`)
    }
  }

  /**
   * Get cache statistics
   */
  async getStats(): Promise<{ totalEntries: number; totalSize: number }> {
    try {
      const files = await fs.readdir(this.cacheDir)
      let totalSize = 0

      for (const file of files) {
        const stats = await fs.stat(path.join(this.cacheDir, file))
        totalSize += stats.size
      }

      return {
        totalEntries: files.length,
        totalSize
      }
    } catch (error) {
      throw new Error(`${ERROR_MESSAGES.CACHE_ERROR}: ${error.message}`)
    }
  }
} 