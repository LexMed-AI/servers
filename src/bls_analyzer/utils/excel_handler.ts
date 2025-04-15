import * as XLSX from 'xlsx'
import { join } from 'path'
import { existsSync } from 'fs'

export interface BLSExcelData {
  socCode: string
  occupationTitle: string
  employmentTotal: number
  meanWage: number
  medianWage: number
  percentiles: {
    p10: number
    p25: number
    p75: number
    p90: number
  }
}

export class BLSExcelHandler {
  private workbook: XLSX.WorkBook | null = null
  private filePath: string
  private static instance: BLSExcelHandler | null = null

  private constructor(filePath: string) {
    this.filePath = filePath
    this.loadWorkbook()
  }

  public static getInstance(filePath: string): BLSExcelHandler {
    if (!BLSExcelHandler.instance) {
      BLSExcelHandler.instance = new BLSExcelHandler(filePath)
    }
    return BLSExcelHandler.instance
  }

  private loadWorkbook(): void {
    if (!existsSync(this.filePath)) {
      throw new Error(`Excel file not found at path: ${this.filePath}`)
    }
    this.workbook = XLSX.readFile(this.filePath)
  }

  public queryBySocCode(socCode: string): BLSExcelData | null {
    if (!this.workbook) {
      throw new Error('Workbook not loaded')
    }

    const sheet = this.workbook.Sheets[this.workbook.SheetNames[0]]
    const data = XLSX.utils.sheet_to_json(sheet)

    const record = data.find((row: any) => row.soc_code === socCode)
    if (!record) return null

    return {
      socCode: record.soc_code,
      occupationTitle: record.occupation_title,
      employmentTotal: record.employment_total,
      meanWage: record.mean_wage,
      medianWage: record.median_wage,
      percentiles: {
        p10: record.p10,
        p25: record.p25,
        p75: record.p75,
        p90: record.p90
      }
    }
  }

  public queryByOccupationTitle(title: string): BLSExcelData[] {
    if (!this.workbook) {
      throw new Error('Workbook not loaded')
    }

    const sheet = this.workbook.Sheets[this.workbook.SheetNames[0]]
    const data = XLSX.utils.sheet_to_json(sheet)

    const records = data.filter((row: any) => 
      row.occupation_title.toLowerCase().includes(title.toLowerCase())
    )

    return records.map((record: any) => ({
      socCode: record.soc_code,
      occupationTitle: record.occupation_title,
      employmentTotal: record.employment_total,
      meanWage: record.mean_wage,
      medianWage: record.median_wage,
      percentiles: {
        p10: record.p10,
        p25: record.p25,
        p75: record.p75,
        p90: record.p90
      }
    }))
  }
} 