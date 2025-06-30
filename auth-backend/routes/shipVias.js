import express from 'express';
import { getShipViasByKeyword } from '../controllers/shipViasController.js';

const router = express.Router();

router.get('/', getShipViasByKeyword);

export default router;
