import express from 'express';
import multer from 'multer';
import { listFiles, uploadFile, deleteFile, downloadFile } from '../controllers/wasabiController.js';

const router = express.Router();
const upload = multer({ dest: 'tmp/' }); // Temporary upload dir

router.get('/list', listFiles);
router.post('/upload', upload.single('file'), uploadFile);
router.delete('/delete', deleteFile);
router.get('/download', downloadFile);

export default router;
