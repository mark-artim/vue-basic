import express from 'express'
import User from '../models/User.js'

const router = express.Router()
// const bcrypt = require('bcrypt')

// GET all users
router.get('/', async (req, res) => {
  const users = await User.find().populate('companyId')
  res.json(users)
})

// GET one user
router.get('/:id', async (req, res) => {
  try {
    const user = await User.findById(req.params.id).populate('companyId')
    if (!user) return res.status(404).json({ error: 'Not found' })
    res.json(user)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

// CREATE user
// router.post('/', async (req, res) => {
//   try {
//     const user = new User(req.body)
//     await user.save()
//     res.status(201).json(user)
//   } catch (err) {
//     res.status(400).json({ error: err.message })
//   }
// })

// Create a new user (ERP or internal)
router.post('/', async (req, res) => {
  try {
    const {
      email,
      password,
      companyId,
      roles = [],
      products = [],
      userType,
      erpUserName,
      firstName,
      lastName,
    } = req.body;

    // Require password only for internal users
    if (userType === 'admin' && !password) {
      return res.status(400).json({ error: 'Password is required for internal users' });
    }

    const hashedPassword =
      userType === 'admin' ? await bcrypt.hash(password, 10) : undefined;

    const user = new User({
      email,
      firstName,
      lastName,
      companyId,
      roles,
      products,
      userType,
      erpUserName,
      ...(hashedPassword && { hashedPassword }), // Only include if it exists
    });
    console.log('[Backend] Incoming request body:', req.body);
    await user.save();
    res.status(201).json(user);
  } catch (err) {
    console.error('Error creating user:', err);
    res.status(400).json({ error: err.message });
  }
});

// UPDATE user
router.put('/:id', async (req, res) => {
  try {
    const user = await User.findByIdAndUpdate(req.params.id, req.body, { new: true, runValidators: true })
    res.json(user)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

// PUT /admin/users/:id/port
router.put('/:id/port', async (req, res) => {
  try {
    const { port } = req.body;
    const user = await User.findByIdAndUpdate(
      req.params.id,
      { lastPort: port },
      { new: true }
    );
    res.json(user);
  } catch (err) {
    console.error('[Update Port Error]', err);
    res.status(500).json({ error: 'Failed to update user port' });
  }
});


// DELETE user
router.delete('/:id', async (req, res) => {
  try {
    await User.findByIdAndDelete(req.params.id)
    res.json({ message: 'Deleted' })
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

export default router
