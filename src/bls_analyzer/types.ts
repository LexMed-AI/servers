export interface DOTSOCCrosswalk {
  dotCode: string
  socCodes: string[]
  timestamp: string
}

export interface OEWSData {
  socCode: string
  employmentTotal: number
  meanWage: number
  medianWage: number
  timestamp: string
  percentiles?: {
    p10?: number
    p25?: number
    p75?: number
    p90?: number
  }
  industries?: Array<{
    naicsCode: string
    employmentTotal: number
    meanWage: number
  }>
}

export interface NAICSCode {
  code: string
  title: string
  level: number
  description?: string
  parentCode?: string
  confidence?: number
}

export interface ScrapingError extends Error {
  url?: string
  statusCode?: number
  selector?: string
  screenshot?: string
} 