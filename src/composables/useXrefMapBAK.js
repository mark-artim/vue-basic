// src/composables/useXrefLoader.js
import { ref } from 'vue'
import Papa from 'papaparse'
import axios from '@/utils/axios'

const edsToHerPN = ref({})
const edsToConvCUS = ref({})

function detectHeaderRow(rows, target) {
  for (let i = 0; i < rows.length; i++) {
    if (rows[i][0]?.startsWith(target)) {
      return i
    }
  }
  return -1
}

async function loadCrossRefFile(key, targetHeader) {
  try {
    console.log(`[xrefLoader] Loading cross-reference file: ${key}`)
    const res = await axios.get('/wasabi/download', {
        params: { filename: `data/uploads/${key}` },
        responseType: 'blob'
    })

    return new Promise((resolve, reject) => {
      Papa.parse(res.data, {
        complete: results => {
          const rows = results.data
          const headerIndex = detectHeaderRow(rows, targetHeader)
          if (headerIndex === -1) return resolve({})

          const header = rows[headerIndex]
          const dataRows = rows.slice(headerIndex + 1)
          const map = {}

          for (const row of dataRows) {
            const from = row[0]?.trim()
            const to = row[1]?.trim()
            if (from && to) {
              map[from] = to
            }
          }
          resolve(map)
        },
        error: reject,
      })
    })
  } catch (err) {
    console.error(`[xrefLoader] Failed to load ${key}:`, err)
    return {}
  }
}

export async function loadCrossReferences() {
  edsToHerPN.value = await loadCrossRefFile('EDS.PN.XREF.csv', 'EDS_PN')
  edsToConvCUS.value = await loadCrossRefFile('EDS.CUS.XREF.csv', 'EDS_CUSNUM')
  console.log('[xrefLoader] Loaded PN and CUS xrefs:', {
    pn: Object.keys(edsToHerPN.value).length,
    cus: Object.keys(edsToConvCUS.value).length
  })
}

export function getHerPN(edsPN) {
  return edsToHerPN.value[edsPN] || null
}

export function getConvCUS(edsCUS) {
  return edsToConvCUS.value[edsCUS] || null
}
