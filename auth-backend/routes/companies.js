// routes/companies.js
import express from 'express'
import Company from '../models/Company.js'

const router = express.Router()

// GET all companies
router.get('/', async (req, res) => {
  const companies = await Company.find()
  res.json(companies)
})

// GET one company
router.get('/:id', async (req, res) => {
  try {
    const company = await Company.findById(req.params.id)
    if (!company) return res.status(404).json({ error: 'Not found' })
    res.json(company)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

// CREATE company
router.post('/', async (req, res) => {
  try {
    const company = new Company(req.body)
    await company.save()
    res.status(201).json(company)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

// UPDATE company
router.put('/:id', async (req, res) => {
  try {
    const company = await Company.findByIdAndUpdate(req.params.id, req.body, { new: true, runValidators: true })
    res.json(company)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

// DELETE company
router.delete('/:id', async (req, res) => {
  try {
    await Company.findByIdAndDelete(req.params.id)
    res.json({ message: 'Deleted' })
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

export default router
