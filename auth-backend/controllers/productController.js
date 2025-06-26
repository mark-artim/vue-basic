import Product from '../models/Product.js'

// GET all products
export const getAllProducts = async (req, res) => {
  try {
    const products = await Product.find()
    res.json(products)
  } catch (err) {
    console.error('Error fetching products:', err)
    res.status(500).json({ error: 'Failed to fetch products' })
  }
}

// CREATE product (optional for admin tools)
export const createProduct = async (req, res) => {
  try {
    const { _id, name, roles = [] } = req.body

    const product = new Product({ _id, name, roles })
    await product.save()

    res.status(201).json(product)
  } catch (err) {
    console.error('Error creating product:', err)
    res.status(400).json({ error: err.message })
  }
}

// UPDATE product
export const updateProduct = async (req, res) => {
  try {
    const update = req.body
    const product = await Product.findByIdAndUpdate(req.params.id, update, {
      new: true,
      runValidators: true
    })

    if (!product) {
      return res.status(404).json({ error: 'Product not found' })
    }

    res.json(product)
  } catch (err) {
    console.error('Error updating product:', err)
    res.status(400).json({ error: err.message })
  }
}


// DELETE product (optional)
export const deleteProduct = async (req, res) => {
  try {
    await Product.findByIdAndDelete(req.params.id)
    res.json({ message: 'Deleted' })
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
}
