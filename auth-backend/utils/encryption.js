import crypto from 'crypto'

const ENCRYPTION_KEY = process.env.SHIPPO_TOKEN_ENCRYPTION_KEY || 'your-32-character-secret-key-here'
const ALGORITHM = 'aes-256-cbc'

export function encryptToken(token) {
  if (!token) return null
  
  try {
    const iv = crypto.randomBytes(16)
    const cipher = crypto.createCipheriv(ALGORITHM, Buffer.from(ENCRYPTION_KEY.substring(0, 32)), iv)
    let encrypted = cipher.update(token, 'utf8', 'hex')
    encrypted += cipher.final('hex')
    
    return iv.toString('hex') + ':' + encrypted
  } catch (err) {
    console.error('Token encryption failed:', err)
    throw new Error('Failed to encrypt token')
  }
}

export function decryptToken(encryptedToken) {
  if (!encryptedToken) return null
  
  try {
    const parts = encryptedToken.split(':')
    if (parts.length !== 2) throw new Error('Invalid encrypted token format')
    
    const iv = Buffer.from(parts[0], 'hex')
    const encrypted = parts[1]
    
    const decipher = crypto.createDecipheriv(ALGORITHM, Buffer.from(ENCRYPTION_KEY.substring(0, 32)), iv)
    let decrypted = decipher.update(encrypted, 'hex', 'utf8')
    decrypted += decipher.final('utf8')
    
    return decrypted
  } catch (err) {
    console.error('Token decryption failed:', err)
    throw new Error('Failed to decrypt token')
  }
}

// Validate Shippo token format
export function isValidShippoTokenFormat(token) {
  if (!token || typeof token !== 'string') return false
  
  // Shippo tokens typically start with shippo_test_ or shippo_live_
  return /^shippo_(test|live)_[a-f0-9]{40}$/.test(token)
}

// Detect token environment
export function getTokenEnvironment(token) {
  if (!token) return null
  if (token.startsWith('shippo_test_')) return 'test'
  if (token.startsWith('shippo_live_')) return 'live'
  return null
}