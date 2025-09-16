import express from 'express'
import Stripe from 'stripe'
import decodeToken from '../middleware/decodeToken.js'
import Company from '../models/Company.js'
import Product from '../models/Product.js'

const router = express.Router()

// Initialize Stripe with secret key from environment
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY)

// Get Stripe configuration (publishable key)
router.get('/config', (req, res) => {
  res.json({
    publishableKey: process.env.STRIPE_PUBLISHABLE_KEY
  })
})

// Create checkout session for product subscription
router.post('/create-checkout-session', decodeToken, async (req, res) => {
  try {
    const { productId, stripeProductId } = req.body
    const userId = req.user.id
    const companyId = req.user.companyId

    console.log('Creating checkout session for:', { productId, stripeProductId, userId, companyId })

    // Validate product exists
    const product = await Product.findById(productId)
    if (!product) {
      return res.status(404).json({ error: 'Product not found' })
    }

    // Check if user already has this product
    const company = await Company.findById(companyId)
    const userProducts = req.user.products || []
    if (userProducts.includes(productId)) {
      return res.status(400).json({ error: 'User already has access to this product' })
    }

    // Create Stripe checkout session
    const session = await stripe.checkout.Session.create({
      ui_mode: 'embedded',
      mode: 'subscription',
      line_items: [{
        price: stripeProductId,
        quantity: 1
      }],
      return_url: `${process.env.FRONTEND_URL}/home?session_id={CHECKOUT_SESSION_ID}`,
      automatic_tax: { enabled: true },
      customer_creation: 'always',
      subscription_data: {
        metadata: {
          userId: userId,
          companyId: companyId,
          productId: productId
        }
      }
    })

    console.log('Stripe session created:', session.id)

    res.json({
      clientSecret: session.client_secret
    })

  } catch (err) {
    console.error('Error creating checkout session:', err)
    res.status(500).json({ 
      error: 'Failed to create checkout session',
      details: err.message
    })
  }
})

// Handle successful subscription webhook
router.post('/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  const sig = req.headers['stripe-signature']
  let event

  try {
    event = stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET)
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message)
    return res.status(400).send(`Webhook Error: ${err.message}`)
  }

  // Handle the event
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object
      await handleSuccessfulSubscription(session)
      break
    }
    
    case 'invoice.payment_succeeded':
      console.log('Payment succeeded for subscription:', event.data.object.subscription)
      break
      
    case 'customer.subscription.deleted': {
      const subscription = event.data.object
      await handleSubscriptionCancellation(subscription)
      break
    }

    default:
      console.log(`Unhandled event type: ${event.type}`)
  }

  res.json({ received: true })
})

// Grant product access after successful subscription
async function handleSuccessfulSubscription(session) {
  try {
    const { userId, companyId, productId } = session.subscription.metadata

    console.log('Granting product access:', { userId, companyId, productId })

    // Add product to user's authorized products
    const company = await Company.findById(companyId)
    if (company) {
      const user = company.users.find(u => u._id.toString() === userId)
      if (user && !user.products.includes(productId)) {
        user.products.push(productId)
        await company.save()
        console.log(`Product ${productId} granted to user ${userId}`)
      }
    }

  } catch (err) {
    console.error('Error handling successful subscription:', err)
  }
}

// Remove product access when subscription is cancelled
async function handleSubscriptionCancellation(subscription) {
  try {
    const { userId, companyId, productId } = subscription.metadata

    console.log('Removing product access:', { userId, companyId, productId })

    const company = await Company.findById(companyId)
    if (company) {
      const user = company.users.find(u => u._id.toString() === userId)
      if (user) {
        user.products = user.products.filter(p => p !== productId)
        await company.save()
        console.log(`Product ${productId} removed from user ${userId}`)
      }
    }

  } catch (err) {
    console.error('Error handling subscription cancellation:', err)
  }
}

export default router