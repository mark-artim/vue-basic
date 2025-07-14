import express from 'express'
import menusRouter from './menus.js'

const router = express.Router()

router.use('/menus', menusRouter)

export default router