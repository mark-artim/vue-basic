import { Resend } from 'resend'
import User from '../models/User.js'
import { generateEmailHtml } from './emailTemplates.js'

const resend = new Resend(process.env.RESEND_API_KEY)

export const sendEmailByType = async (toEmail, userId, type = 'standard') => {
  const user = await User.findById(userId).populate('companyId')
  if (!user) {
    throw new Error('User not found')
  }

  const subjectMap = {
    standard: `Welcome to EMP54!`,
    heritage: `Welcome to Heritage Eclipse Portal`,
    reset: `Reset Your Password`
  }

  const html = generateEmailHtml(user, type)
  const subject = subjectMap[type] || 'EMP54 Notification'

  const result = await resend.emails.send({
    from: 'Emp54 <info@emp54.com>',
    to: toEmail,
    subject,
    html
  })

  return result
}
