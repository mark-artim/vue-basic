import express from 'express';
import multer from 'multer';
import { listFiles, uploadFile, deleteFile, downloadFile, renameFile } from '../controllers/wasabiController.js';

const router = express.Router();
const upload = multer({ dest: 'tmp/' }); // Temporary upload dir

router.get('/list', listFiles);
router.post('/upload', upload.single('file'), uploadFile);
router.delete('/delete', deleteFile);
router.get('/download', downloadFile);
router.post('/rename', renameFile);

export default router;
