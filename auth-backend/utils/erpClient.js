import axios from 'axios'
import https from 'https'

export default function erpClient({ baseUrl, port, token, log = false }) {
  const finalUrl = `${baseUrl}:${port}`

  if (log) {
    console.log('[erpClient] Created ERP client for', finalUrl)
  }

  // Reuse connections to reduce socket exhaustion
  const httpsAgent = new https.Agent({
    keepAlive: true,
    maxSockets: 20,      // adjust based on load
    timeout: 30000
  })

  return axios.create({
    baseURL: finalUrl,
    timeout: 30000,
    httpsAgent,
    headers: {
      Authorization: `SessionToken ${decodeURIComponent(token)}`,
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
  })
}
