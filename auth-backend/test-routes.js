import express from 'express'
import erpRoutes from './routes/erp.js'

const app = express()
app.use('/erp', erpRoutes)

// List all routes
function listRoutes(app) {
  console.log('Registered routes:')
  app._router.stack.forEach(function(r){
    if (r.route && r.route.path){
      console.log(`${Object.keys(r.route.methods).join(',').toUpperCase()} ${r.route.path}`)
    } else if (r.name === 'router') {
      console.log('Router middleware:')
      r.handle.stack.forEach(function(route) {
        if (route.route) {
          console.log(`  ${Object.keys(route.route.methods).join(',').toUpperCase()} /erp${route.route.path}`)
        }
      })
    }
  })
}

listRoutes(app)