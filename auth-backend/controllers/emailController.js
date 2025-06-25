import { sendEmailByType } from '../services/emailService.js'

export const sendEmail = async (req, res) => {
  const { toEmail, userId, templateType = 'standard' } = req.body

  console.log('📨 [sendEmail] Received request:', { toEmail, userId, templateType })

  if (!toEmail || !userId) {
    return res.status(400).json({ message: 'Missing toEmail or userId' })
  }

  try {
    const result = await sendEmailByType(toEmail, userId, templateType) // ✅ use correct function
    res.json({ success: true, result })
  } catch (error) {
    console.error('❌ Email sending failed:', error)
    res.status(500).json({ success: false, message: error.message })
  }
}
