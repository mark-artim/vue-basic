// controllers/logController.js
import Log from '../models/Log.js';

export const getLogs = async (req, res) => {
  try {
    const { type, email, limit = 100 } = req.query;

    const query = {};
    if (type) query.type = type;
    if (email) query.userEmail = { $regex: new RegExp(email, 'i') };

    const logs = await Log.find(query)
      .sort({ timestamp: -1 })
      .limit(parseInt(limit));

    res.json(logs);
  } catch (err) {
    console.error('[Log Viewer Error]', err);
    res.status(500).json({ error: 'Failed to fetch logs' });
  }
};
