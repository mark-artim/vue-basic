import axios from 'axios'

const PYTHON_BASE_URL = import.meta.env.VITE_PYTHON_API_BASE_URL || 'http://localhost:5000'
console.log('[Python Client] Base URL:', PYTHON_BASE_URL)

const pythonClient = axios.create({
  baseURL: PYTHON_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default pythonClient
