import User from '../models/User.js'
import bcrypt from 'bcrypt'

// GET all users
export const getAllUsers = async (req, res) => {
  const users = await User.find().populate('companyId')
  res.json(users)
}

// GET one user by ID
export const getUserById = async (req, res) => {
  try {
    const user = await User.findById(req.params.id).populate('companyId')
    if (!user) return res.status(404).json({ error: 'Not found' })
    res.json(user)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
}

// CREATE new user
export const createUser = async (req, res) => {
  try {
    const {
      email, password, companyId,
      roles = {},                 // now a product → roles map
      products = Object.keys(roles), // default: keys from roles
      userType, erpUserName, firstName, lastName
    } = req.body


    if (userType === 'admin' && !password) {
      return res.status(400).json({ error: 'Password is required for internal users' })
    }

    const hashedPassword = userType === 'admin' ? await bcrypt.hash(password, 10) : undefined

    const user = new User({
      email, firstName, lastName, companyId, roles, products,
      userType, erpUserName,
      ...(hashedPassword && { hashedPassword }),
    })

    await user.save()
    res.status(201).json(user)
  } catch (err) {
    console.error('Error creating user:', err)
    res.status(400).json({ error: err.message })
  }
}

// UPDATE user
export const updateUser = async (req, res) => {
  try {
    const update = req.body
    if (!update.products && update.roles) {
      update.products = Object.keys(update.roles)
    }

    const user = await User.findByIdAndUpdate(req.params.id, update, {
      new: true, runValidators: true
    })

    res.json(user)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
}

// UPDATE user's last used port
export const updateUserPort = async (req, res) => {
  try {
    const { port } = req.body
    const user = await User.findByIdAndUpdate(
      req.params.id,
      { lastPort: port },
      { new: true }
    )
    res.json(user)
  } catch (err) {
    console.error('[Update Port Error]', err)
    res.status(500).json({ error: 'Failed to update user port' })
  }
}

// DELETE user
export const deleteUser = async (req, res) => {
  try {
    await User.findByIdAndDelete(req.params.id)
    res.json({ message: 'Deleted' })
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
}
