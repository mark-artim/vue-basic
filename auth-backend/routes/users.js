import express from 'express'
import {
  getAllUsers,
  getUserById,
  createUser,
  updateUser,
  updateUserPort,
  deleteUser
} from '../controllers/userController.js'

const router = express.Router()

router.get('/', getAllUsers)
router.get('/:id', getUserById)
router.post('/', createUser)
router.put('/:id', updateUser)
router.put('/:id/port', updateUserPort)
router.delete('/:id', deleteUser)

export default router
