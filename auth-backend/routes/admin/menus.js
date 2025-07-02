import express from 'express'
import { getAllMenus } from '../../controllers/menuController.js'

const router = express.Router()

router.get('/', getAllMenus) // no decodeToken (or add one if you want)

export default router
