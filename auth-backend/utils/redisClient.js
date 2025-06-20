// utils/redisClient.js
import 'dotenv/config'
console.log('[redisClient] URL:', process.env.UPSTASH_REDIS_REST_URL)
console.log('[redisClient] TOKEN:', process.env.UPSTASH_REDIS_REST_TOKEN)

import { Redis } from '@upstash/redis'

const redis = Redis.fromEnv()  // Reads UPSTASH_REDIS_REST_URL & TOKEN
export default redis
