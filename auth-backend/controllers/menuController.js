import Menu from '../models/Menu.js'
import Company from '../models/Company.js'
import User from '../models/User.js'

// This controller handles menu-related operations, including filtering menus based on user roles and company products.
export const getFilteredMenus = async (req, res) => {
  try {
    const userId = req.user?.userId
    if (!userId) return res.status(401).json({ error: 'Unauthorized' })

    const user = await User.findById(userId).lean()
    const company = await Company.findById(user.companyId)

    const entitledProducts = company.products
    const userRoles = user.roles || {}
    // console.log('[getFilteredMenus] Cleaned userRoles:', userRoles)


    const menus = await Menu.find({ product: { $in: entitledProducts } })

    // console.log('[getFilteredMenus] company.products:', entitledProducts)
    // console.log('[getFilteredMenus] user.roles:', JSON.stringify(userRoles, null, 2))
    // console.log('[getFilteredMenus] all menus:', menus.map(m => `${m.name} (${m.product})`))

    const visibleMenus = menus.filter(menu => {
      const allowedRoles = menu.roles || []
      const userRolesForProduct = userRoles[menu.product] || []

      // console.log(`Checking menu: ${menu.name}`)
      // console.log(' - product:', menu.product)
      // console.log(' - allowed roles:', allowedRoles)
      // console.log(' - user roles for product:', userRolesForProduct)

      return userRolesForProduct.some(role => allowedRoles.includes(role))
    })

    // console.log('[getFilteredMenus] visible menus:', visibleMenus.map(m => m.name))

    res.json(visibleMenus)
  } catch (err) {
    console.error('[getFilteredMenus] Error:', err)
    res.status(500).json({ error: 'Failed to load menus' })
  }
}

export const getAllMenus = async (req, res) => {
  try {
    const menus = await Menu.find().lean()
    res.json(menus)
  } catch (err) {
    console.error('[getAllMenus] Error:', err)
    res.status(500).json({ message: 'Failed to fetch all menus' })
  }
}

export const createMenu = async (req, res) => {
  try {
    const { name, path, product, roles } = req.body

    if (!name || !path || !product || !Array.isArray(roles)) {
      return res.status(400).json({ message: 'Missing required fields.' })
    }

    const existing = await Menu.findOne({ path, product })
    if (existing) {
      return res.status(409).json({ message: 'Menu with this path/product already exists.' })
    }

    const menu = new Menu({ name, path, product, roles })
    await menu.save()
    res.status(201).json(menu)
  } catch (err) {
    console.error('[createMenu] Error:', err)
    res.status(500).json({ message: 'Failed to create menu.' })
  }
}
