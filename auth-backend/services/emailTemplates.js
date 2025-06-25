export function generateEmailHtml(user, type) {
  const { firstName, email } = user

  switch (type) {
    case 'heritage':
      return `
        <h2>Welcome to the Eclipse - Heritage Portal</h2>
        <p>Hi ${firstName || 'there'},</p>
        <p>You’ve been granted access to our <strong>Heritage Eclipse Portal</strong>.</p>
        <p>Your login is: <strong>${email}</strong></p>
        <p>Use your Eclipse password to log in. (yes - the email above and your current Eclipse password)</strong>.</p>
        <p><a href="https://www.emp54.com/login">Access the Heritage Eclipse Portal</a></p>
      `

    case 'reset':
      return `
        <h2>Password Reset</h2>
        <p>Hi ${firstName || 'there'},</p>
        <p>You requested a password reset. Use the link below to create a new password:</p>
        <p><a href="https://vue-basic-production.up.railway.app/reset-password">Reset Your Password</a></p>
      `

    case 'standard':
    default:
      return `
        <h2>Welcome to EMP54</h2>
        <p>Hi ${firstName || 'there'},</p>
        <p>Your account has been created. You can log in using your email:</p>
        <p><strong>${email}</strong></p>
        <p>Use your Eclipse password to log in. (yes - the email above and your current Eclipse password)</strong>.</p>
        <p><a href="https://www.emp54.com/login">Log In</a></p>
      `
  }
}
