import fs from 'fs';
import path from 'path';
import AWS from 'aws-sdk';
import dotenv from 'dotenv';
import Stream from 'stream';

dotenv.config();

const {
  WASABI_ACCESS_KEY,
  WASABI_SECRET_KEY,
  WASABI_REGION,
  WASABI_ENDPOINT,
  WASABI_BUCKET
} = process.env;

console.log('[Wasabi] Configuring Wasabi S3 client with bucket:', WASABI_BUCKET);
console.log('[Wasabi] Using region:', WASABI_REGION || 'us-east-1');
console.log('[Wasabi] Using endpoint:', WASABI_ENDPOINT || 'https://s3.wasabisys.com');
console.log('[Wasabi] Access Key:', WASABI_ACCESS_KEY ? '***' : 'Not Set');
console.log('[Wasabi] Secret Key:', WASABI_SECRET_KEY ? '***' : 'Not Set');

const s3 = new AWS.S3({
  accessKeyId: WASABI_ACCESS_KEY,
  secretAccessKey: WASABI_SECRET_KEY,
  region: WASABI_REGION || 'us-east-1',
  endpoint: WASABI_ENDPOINT || 'https://s3.wasabisys.com',
});

export const listFiles = async (req, res) => {
  try {
    const data = await s3.listObjectsV2({ Bucket: WASABI_BUCKET }).promise();
    const files = data.Contents.map(obj => ({
      key: obj.Key,
      size: obj.Size,
      lastModified: obj.LastModified
    }));
    res.json({ files });
  } catch (err) {
    console.error('[Wasabi] Failed to list files:', err);
    res.status(500).json({ error: 'Failed to list files' });
  }
};

export const uploadFile = async (req, res) => {
  const file = req.file;
  if (!file) return res.status(400).json({ error: 'No file uploaded' });

  const fileStream = fs.createReadStream(file.path);
  const uploadParams = {
    Bucket: WASABI_BUCKET,
    Key: `data/uploads/${file.originalname}`,
    Body: fileStream,
  };

  try {
    await s3.upload(uploadParams).promise();
    fs.unlinkSync(file.path); // Clean up temp file
    res.json({ message: `Uploaded ${file.originalname}` });
  } catch (err) {
    console.error('[Wasabi] Upload failed:', err);
    res.status(500).json({ error: 'Upload failed' });
  }
};

export const deleteFile = async (req, res) => {
  const { key } = req.body;
  if (!key) return res.status(400).json({ error: 'Missing file key' });

  try {
    await s3.deleteObject({ Bucket: WASABI_BUCKET, Key: key }).promise();
    res.json({ message: `Deleted ${key}` });
  } catch (err) {
    console.error('[Wasabi] Delete failed:', err);
    res.status(500).json({ error: 'Delete failed' });
  }
};

export const downloadFile = async (req, res) => {
  const filename = req.query.filename;
  if (!filename) {
    return res.status(400).json({ error: 'Missing filename' });
  }

  const downloadParams = {
    Bucket: WASABI_BUCKET,
    Key: filename,
  };

  try {
    const fileStream = s3.getObject(downloadParams).createReadStream();

    // Pipe the file to the response
    res.setHeader('Content-Type', 'application/octet-stream');
    fileStream.pipe(res);
  } catch (err) {
    console.error('[Wasabi] Download failed:', err);
    res.status(500).json({ error: 'Download failed' });
  }
};