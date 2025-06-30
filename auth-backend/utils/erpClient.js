import axios from 'axios'
import https from 'https'

export default function erpClient({ baseUrl, port, token, log = false }) {
  const finalUrl = `${baseUrl}:${port}`

  if (log) {
    console.log('[erpClient] Created ERP client for', finalUrl)
  }

  // Reuse connections to reduce socket exhaustion
    const agent = new https.Agent({
    keepAlive: true,
    maxSockets: 50,            // Increase from default 25
    maxFreeSockets: 20,        // Increase from default 5
    timeout: 60000,            // Optional socket timeout
  });

  return axios.create({
    baseURL: finalUrl,
    timeout: 30000,
    httpsAgent: agent,
    headers: {
      Authorization: `SessionToken ${decodeURIComponent(token)}`,
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
  })
}
