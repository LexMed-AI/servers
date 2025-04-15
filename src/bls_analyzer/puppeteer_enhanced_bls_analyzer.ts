import puppeteer, { Browser, Page } from 'puppeteer'
import { BLSAnalyzer } from './bls_analyzer.js'
import { DOTSOCCrosswalk, OEWSData, NAICSCode } from './types.js'
import { delay, sanitizeInput } from '../sqlite/src/mcp_server_sqlite/utils/helpers.js'
import path from 'path'
import fs from 'fs'

export class PuppeteerEnhancedBLSAnalyzer extends BLSAnalyzer {
  private browser: Browser | null = null
  private page: Page | null = null
  private readonly screenshotsDir: string
  private readonly cacheDir: string
  private readonly CACHE_DURATION = 24 * 60 * 60 * 1000 // 24 hours in milliseconds

  constructor(
    apiKey: string,
    screenshotsDir = path.join(__dirname, 'screenshots'),
    cacheDir = path.join(__dirname, 'cache')
  ) {
    super(apiKey)
    this.screenshotsDir = screenshotsDir
    this.cacheDir = cacheDir
    this.ensureDirectories()
  }

  private ensureDirectories(): void {
    [this.screenshotsDir, this.cacheDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true })
      }
    })
  }

  async initialize(): Promise<void> {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      })
      this.page = await this.browser.newPage()
      await this.page.setViewport({ width: 1920, height: 1080 })
    }
  }

  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close()
      this.browser = null
      this.page = null
    }
  }

  private async takeScreenshot(name: string): Promise<string> {
    if (!this.page) throw new Error('Browser not initialized')
    
    const filename = `${name}_${Date.now()}.png`
    const filepath = path.join(this.screenshotsDir, filename)
    await this.page.screenshot({ path: filepath, fullPage: true })
    return filepath
  }

  private getCachePath(key: string): string {
    return path.join(this.cacheDir, `${sanitizeInput(key)}.json`)
  }

  private async getCachedData<T>(key: string): Promise<T | null> {
    const cachePath = this.getCachePath(key)
    if (!fs.existsSync(cachePath)) return null

    const cacheData = JSON.parse(fs.readFileSync(cachePath, 'utf-8'))
    const age = Date.now() - cacheData.timestamp

    if (age > this.CACHE_DURATION) {
      fs.unlinkSync(cachePath)
      return null
    }

    return cacheData.data as T
  }

  private async setCachedData<T>(key: string, data: T): Promise<void> {
    const cachePath = this.getCachePath(key)
    const cacheData = {
      timestamp: Date.now(),
      data
    }
    fs.writeFileSync(cachePath, JSON.stringify(cacheData))
  }

  async getDOTSOCCrosswalk(dotCode: string): Promise<DOTSOCCrosswalk> {
    const cacheKey = `dot_soc_${dotCode}`
    const cached = await this.getCachedData<DOTSOCCrosswalk>(cacheKey)
    if (cached) return cached

    await this.initialize()
    if (!this.page) throw new Error('Browser not initialized')

    try {
      // Implementation for scraping DOT-SOC crosswalk data
      // This is a placeholder - actual implementation will depend on the specific website structure
      const crosswalk: DOTSOCCrosswalk = {
        dotCode,
        socCodes: [],
        timestamp: new Date().toISOString()
      }

      await this.setCachedData(cacheKey, crosswalk)
      await this.takeScreenshot(`dot_soc_${dotCode}`)
      return crosswalk
    } catch (error) {
      console.error('Error fetching DOT-SOC crosswalk:', error)
      throw error
    }
  }

  async getOEWSData(socCode: string): Promise<OEWSData> {
    const cacheKey = `oews_${socCode}`
    const cached = await this.getCachedData<OEWSData>(cacheKey)
    if (cached) return cached

    await this.initialize()
    if (!this.page) throw new Error('Browser not initialized')

    try {
      // Implementation for scraping OEWS data
      // This is a placeholder - actual implementation will depend on the specific website structure
      const oewsData: OEWSData = {
        socCode,
        employmentTotal: 0,
        meanWage: 0,
        medianWage: 0,
        timestamp: new Date().toISOString()
      }

      await this.setCachedData(cacheKey, oewsData)
      await this.takeScreenshot(`oews_${socCode}`)
      return oewsData
    } catch (error) {
      console.error('Error fetching OEWS data:', error)
      throw error
    }
  }

  async inferNAICSCodes(jobDescription: string): Promise<NAICSCode[]> {
    const cacheKey = `naics_${jobDescription.slice(0, 50)}`
    const cached = await this.getCachedData<NAICSCode[]>(cacheKey)
    if (cached) return cached

    await this.initialize()
    if (!this.page) throw new Error('Browser not initialized')

    try {
      // Implementation for inferring NAICS codes
      // This is a placeholder - actual implementation will depend on the specific website structure
      const naicsCodes: NAICSCode[] = []

      await this.setCachedData(cacheKey, naicsCodes)
      await this.takeScreenshot(`naics_inference_${Date.now()}`)
      return naicsCodes
    } catch (error) {
      console.error('Error inferring NAICS codes:', error)
      throw error
    }
  }
} 