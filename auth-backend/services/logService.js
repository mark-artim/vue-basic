/// services/logService.js
import Log from '../models/Log.js';

export async function logEvent({ userId, userEmail, companyId, companyCode, type, source = 'auth-backend', message, meta = {} }) {
  await Log.create({
    userId,
    userEmail,
    companyId,
    companyCode,
    type,
    source,
    message,
    meta
  });
}
