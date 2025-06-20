// server.js
import app from './app.js'

const PORT = process.env.PORT || 3001
app.listen(PORT, () => {
  console.log(`Auth backend running on port ${PORT}`)
})
