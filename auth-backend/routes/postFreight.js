import express from 'express';
import { postFreightHandler } from '../controllers/postFreightController.js';

const router = express.Router();

router.post('/', postFreightHandler);

export default router;