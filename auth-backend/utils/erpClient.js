// utils/erpClient.js
import axios from 'axios';

export default function erpClient({ baseUrl, port, token, log = false }) {
  const finalUrl = `${baseUrl}:${port}`;

  if (log) {
    console.log('[erpClient] Created ERP client for', finalUrl);
  }

  return axios.create({
    baseURL: finalUrl,
    timeout: 30000,
    headers: {
      Authorization: `SessionToken ${decodeURIComponent(token)}`,
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
  });
}
