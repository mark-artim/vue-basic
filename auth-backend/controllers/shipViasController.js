import axios from 'axios';
import jwt from 'jsonwebtoken';

export const getShipViasByKeyword = async (req, res) => {
  const { keyword } = req.query;

  if (!keyword) {
    return res.status(400).json({ error: 'Missing keyword' });
  }

  try {
    const token = req.headers.authorization?.split(' ')[1];
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const port = decoded.lastPort || 5000;

    const proxyResponse = await axios.post(
      'http://localhost:3001/api/erp-proxy', // or use full URL to your API host
      {
        method: 'GET',
        url: `/ShipVias?keyword=${encodeURIComponent(keyword)}`,
        port
      },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    res.json(proxyResponse.data);
  } catch (err) {
    console.error('[ShipVias Controller] Failed:', err.message);
    res.status(500).json({ error: 'Failed to fetch ShipVias' });
  }
};
