import express from 'express'
import { getFilteredMenus } from '../controllers/menuController.js'
import decodeToken from '../middleware/decodeToken.js'  // ✅ import it

const router = express.Router()

router.get('/', decodeToken, getFilteredMenus)  // ✅ protect the route

export default router
