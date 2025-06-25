import { Resend } from 'resend'
import { getUserById } from '../services/userService.js'
import { generateEmailHtml } from '../services/emailTemplates.js'

const resend = new Resend(process.env.RESEND_API_KEY)

export async function sendWelcomeEmail(toEmail, userId, templateType = 'standard') {
  console.log(`[sendWelcomeEmail] Sending welcome email to ${toEmail} with template: ${templateType}`)
  const user = await getUserById(userId)
  if (!user) {
    throw new Error(`User not found for ID: ${userId}`)
  }

  const html = generateEmailHtml(user, templateType)

  const subjectMap = {
    standard: 'Welcome to EMP54!',
    heritage: 'Welcome to EMP54 - Heritage Portal Access',
    reset: 'Reset Your Password'
  }

  const subject = subjectMap[templateType] || 'Welcome to EMP54!'

  const result = await resend.emails.send({
    from: 'info@emp54.com',
    to: toEmail,
    subject,
    html
  })

  return result
}
