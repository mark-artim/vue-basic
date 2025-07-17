import jwt from 'jsonwebtoken';

export function generateToken(user, erpToken = null, userType = 'customer') {
  return jwt.sign(
    {
      userId: user._id,
      companyId: user.companyId,
      companyCode: user.companyId?.companyCode,
      apiBaseUrl: user.companyId.apiBaseUrl,
      roles: user.roles,
      products: user.products,
      userType,
      lastPort: user.lastPort,
      erpUserName: user.erpUserName,
      ...(erpToken && { erpToken })
    },
    process.env.JWT_SECRET,
    { expiresIn: '2h' }
  )
}
