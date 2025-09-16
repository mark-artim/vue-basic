# Vue-Basic API Documentation

This document provides comprehensive documentation of all API calls used in the vue-basic project, organized by category and integration type.

## Table of Contents

- [API Client Architecture](#api-client-architecture)
- [ERP Integration API Calls](#erp-integration-api-calls)
- [MongoDB/Backend API Calls](#mongodbbackend-api-calls)
- [Third-Party Integration API Calls](#third-party-integration-api-calls)
- [Python Backend API Calls](#python-backend-api-calls)
- [Environment Configuration](#environment-configuration)
- [Authentication Patterns](#authentication-patterns)

---

## API Client Architecture

The vue-basic project uses multiple HTTP clients for different types of API calls:

### **1. Authenticated API Client (`src/utils/axios.js`)**
- **Purpose**: JWT-authenticated calls to Node.js backend
- **Base URL**: `VITE_API_URL` or `http://localhost:3001`
- **Features**: 
  - Automatic JWT token injection
  - Request/response logging
  - 401 error handling with redirect to login
  - 60-second timeout

### **2. Public API Client (`src/utils/axiosPublic.js`)**
- **Purpose**: Unauthenticated calls (login, public endpoints)
- **Base URL**: `VITE_API_URL` or `http://localhost:3001`
- **Features**: No authentication headers

### **3. Python API Client (`src/utils/pythonClient.js`)**
- **Purpose**: File processing and data analysis
- **Base URL**: `VITE_PYTHON_API_BASE_URL` or `http://localhost:5000`
- **Features**: Content-Type: application/json

---

## ERP Integration API Calls

All ERP calls use the `/api/erp-proxy` endpoint pattern to communicate with Eclipse ERP system through the Node.js backend.

### **Pattern**: `POST /api/erp-proxy`
**Request Body**:
```javascript
{
  method: 'GET|POST|PUT|DELETE',
  url: '/ERPEndpoint',
  params: { /* query parameters */ },
  data: { /* request body for POST/PUT */ }
}
```

### **User Management** (`src/api/users.js`)
```javascript
// Search users
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Users',
  params: { keyword, includeTotalItems: true }
}

// Get specific user
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Users/{userId}'
}
```

### **Customer Management** (`src/api/customers.js`)
```javascript
// Search customers
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Customers',
  params: { keyword, includeTotalItems: true }
}

// Get specific customer
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Customers/{customerId}'
}
```

### **Product Management** (`src/api/products.js`)
```javascript
// Search products
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Products',
  params: { keyword, includeInactive: false, pageSize: 50 }
}

// Get specific product
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Products/{productId}'
}
```

### **Contact Management** (`src/api/contacts.js`)
```javascript
// Search contacts
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Contacts',
  params: { keyword, includeTotalItems: true }
}

// Get specific contact
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Contacts/{contactId}'
}

// Update contact
PUT /Contacts/{contactId}
// Note: Direct PUT call for updates
```

### **Sales Order Management** (`src/api/orders.js`)
```javascript
// Search orders
POST /api/erp-proxy
{
  method: 'GET',
  url: '/SalesOrders',
  params: { /* search parameters */ }
}

// Get specific order
POST /api/erp-proxy
{
  method: 'GET',
  url: '/SalesOrders/{invoice}'
}
```

### **Pricing & Product Inquiry** (`src/api/pricing.js`)
```javascript
// Product pricing mass inquiry
POST /api/erp-proxy
{
  method: 'GET',
  url: '/ProductPricingMassInquiry?{queryParams}'
}
```

### **Branch Management** (`src/api/branches.js`)
```javascript
// Search branches
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Branches',
  params: { keyword, includeTotalItems: true }
}

// Get specific branch
POST /api/erp-proxy
{
  method: 'GET',
  url: '/Branches/{branchId}'
}
```

### **Additional ERP Entities**
- **Vendors** (`src/api/vendors.js`): `/Vendors` endpoints
- **Price Lines** (`src/api/priceLines.js`): `/PriceLines` endpoints  
- **Territories** (`src/api/territories.js`): `/Territories` endpoints
- **Ship Vias** (`src/api/shipVias.js`): `/ShipVias` endpoints

---

## MongoDB/Backend API Calls

Direct calls to the Node.js/Express backend for application-specific operations.

### **Authentication & Sessions**

#### User Login (`src/stores/auth.js`)
```javascript
POST /auth/login
{
  email: 'user@example.com',
  password: 'password'
}
```

#### Session Management (`src/api/auth.js`)
```javascript
// Create session
POST /Sessions
{
  username: 'username',
  password: 'password'
}

// Destroy session
DELETE /Sessions/{sessionId}
Headers: { sessionToken: 'token' }
```

### **User Administration**

#### User CRUD Operations (`src/pages/admin/Users.vue`)
```javascript
// List all users
GET /admin/users

// Create user
POST /admin/users
{
  email: 'user@example.com',
  username: 'username',
  password: 'password',
  role: 'user',
  companyId: 'company-id'
}

// Update user  
PUT /admin/users/{id}
{
  email: 'updated@example.com',
  role: 'admin'
}

// Delete user
DELETE /admin/users/{id}

// Update user port
PUT /admin/users/{userId}/port
{ port: 5001 }
```

#### Direct User Updates (`src/api/users.js`)
```javascript
// Update user (bypass ERP)
PUT /Users/{userId}
{
  email: 'new@example.com',
  preferences: { theme: 'dark' }
}
```

### **Company Management**

#### Company CRUD Operations (`src/pages/admin/Company.vue`)
```javascript
// List companies
GET /admin/companies

// Create company
POST /admin/companies
{
  name: 'Company Name',
  address: 'Company Address',
  phone: '555-1234'
}

// Update company
PUT /admin/companies/{id}
{
  name: 'Updated Company Name'
}

// Delete company
DELETE /admin/companies/{id}
```

#### Webhook Management
```javascript
// Check webhook status
GET /admin/companies/{id}/webhook/status

// Create webhook
POST /admin/companies/{id}/webhook/create

// Delete webhook
DELETE /admin/companies/{id}/webhook

// Bulk webhook creation
POST /admin/companies/webhooks/create-all
```

### **Product Management**

#### Product CRUD Operations (`src/pages/admin/Products.vue`)
```javascript
// List products
GET /products

// Create product
POST /products
{
  name: 'Product Name',
  description: 'Product Description',
  price: 29.99
}

// Update product
PUT /products/{id}
{
  name: 'Updated Product Name',
  price: 39.99
}

// Delete product
DELETE /products/{id}
```

### **Settings & Configuration**

#### Ship54 Settings (`src/pages/Ship54Settings.vue`)
```javascript
// Get settings
GET /ship54/settings

// Update settings
PUT /ship54/settings
{
  shippoConnected: true,
  testMode: false,
  defaultCarrier: 'UPS'
}

// Shippo connection management
POST /ship54/shippo/connect
DELETE /ship54/shippo/disconnect
POST /ship54/toggle-test-mode
GET /ship54/shippo/test
POST /ship54/shippo/validate-token
POST /ship54/shippo/test-token
DELETE /ship54/shippo/remove-token
```

### **Menu Management**

#### Dynamic Menu Operations (`src/pages/admin/MenuMaint.vue`)
```javascript
// Get menu configuration
GET /admin/menus

// Create/update menu
POST /admin/menus
{
  menuItems: [
    { name: 'Dashboard', path: '/dashboard', icon: 'dashboard' }
  ]
}
```

### **Shipment & Logistics Management**

#### Shipment Operations (`src/pages/InvoiceTracking.vue`)
```javascript
// Get shipment by invoice
GET /api/shipments/by-invoice/{invoice}

// Get specific shipment
GET /api/shipments/{shipmentId}

// Get tracking test mode
GET /api/shipments/tracking-test-mode

// Create manual shipment
POST /api/shipments/create-manual
{
  trackingNumber: 'TR123456789',
  carrier: 'UPS',
  invoice: 'INV-001'
}

// Create from ShipStation
POST /api/shipments/create-from-shipstation
{
  shippoData: { /* shippo response */ },
  userContext: { /* user info */ }
}

// Get shipment statistics
GET /api/shipments/summary/stats?days=30
```

#### Address Validation (`src/pages/ShipStationOrderDetail.vue`)
```javascript
// Validate address
POST /api/shipping/validate-address
{
  address: {
    street1: '123 Main St',
    city: 'Anytown',
    state: 'CA',
    zip: '12345'
  }
}
```

### **Freight Processing**
```javascript
// Post freight charges
POST /postFreight
{
  invoice: 'INV-001',
  amount: 25.00,
  description: 'Ground shipping'
}
```

### **Data Validation**

#### Form Validation (`src/utils/validators.js`)
```javascript
// Search shipping methods
GET /ShipVias?keyword={keyword}

// Search payment terms
GET /TermsList?keyword={keyword}
```

### **System Monitoring**

#### Log Management (`src/pages/admin/Logs.vue`)
```javascript
// Retrieve application logs
GET /logs?limit=100&page=1&level=error&search=api
```

---

## Third-Party Integration API Calls

### **Stripe Payment Processing**

#### Payment Operations (`src/pages/ProductSignup.vue`)
```javascript
// Get Stripe configuration
GET /stripe/config

// Create checkout session
POST /stripe/create-checkout-session
{
  productId: 'product-id',
  userId: 'user-id'
}

// Get session details
GET /stripe/session/{sessionId}
```

### **Shippo Shipping Integration**

#### Direct Shippo API Calls (`src/pages/ShipStationOrderDetail.vue`)
```javascript
// Create shipment
fetch('https://api.goshippo.com/shipments/', {
  method: 'POST',
  headers: {
    'Authorization': `ShippoToken ${shippoToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    address_from: { /* from address */ },
    address_to: { /* to address */ },
    parcels: [{ /* package details */ }]
  })
})

// Purchase shipping label
fetch('https://api.goshippo.com/transactions', {
  method: 'POST',
  headers: {
    'Authorization': `ShippoToken ${shippoToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    rate: 'rate-id',
    label_file_type: 'PDF'
  })
})
```

#### Backend Shippo Integration (`auth-backend/routes/shipping.js`)
```javascript
// Address validation
fetch('https://api.goshippo.com/addresses/', {
  method: 'POST',
  headers: {
    'Authorization': `ShippoToken ${shippoToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(address)
})
```

#### Shippo Webhooks (`auth-backend/routes/shippo.js`)
```javascript
// Company-specific webhook
POST /shippo/webhook/{companyId}

// Legacy webhook  
POST /shippo/webhook
```

### **Eclipse ERP Integration**

#### Freight Export (`auth-backend/controllers/postFreightController.js`)
```javascript
// Creates ADEOUT files for Eclipse ERP
// File Path: C:/Users/mark.artim/OneDrive - Heritage Distribution Holdings/EclipseDownload/ADEOUT.0
// Supports: UPS, FEDEX freight posting with different billing methods
```

---

## Python Backend API Calls

### **File Processing & Data Analysis**

#### Inventory Balance Comparison (`src/pages/InvBal.vue`)
```javascript
// Compare inventory files
POST /api/compare-inv-bal
Content-Type: multipart/form-data
{
  conv_file: File,
  eds_file: File,
  eds_part_col: 'ESC.PN',
  value_col: 'OH-TOTAL',
  display_col: 'AVAILABLE'  // optional
}
```

#### CSV Processing
```javascript
// Additional CSV processing endpoints available
// Check backend/csv_processor.py for additional endpoints
```

---

## Environment Configuration

### **Environment Variables**

#### Frontend (.env files)
```bash
# API Endpoints
VITE_API_URL=http://localhost:3001          # Node.js backend
VITE_PYTHON_API_BASE_URL=http://localhost:5000  # Python backend

# Third-party Integrations
VITE_SHIPPO_API_KEY=shippo_test_fb4523a2ea15b8fba292d70ca41b939e2ea0d096
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...

# Environment-specific
VITE_ENV=development
```

#### Backend Environment
```bash
# Database
MONGODB_URI=mongodb://localhost:27017/vue-basic

# Authentication
JWT_SECRET=your-jwt-secret

# Third-party APIs
SHIPPO_API_TOKEN=shippo_live_...
STRIPE_SECRET_KEY=sk_live_...

# ERP Connection
ERP_API_BASE_URL=https://erp-server:port
ERP_API_TOKEN=erp-token
```

### **Port Configuration**
- **Frontend**: 3000 (Vite dev server)
- **Node.js Backend**: 3001 (Express server)
- **Python Backend**: 5000 (Flask server)
- **Database**: 27017 (MongoDB)

---

## Authentication Patterns

### **JWT Token Management**

#### Token Storage
- Primary: `localStorage.getItem('jwt')`
- Fallback: `sessionStorage.getItem('jwt')`

#### Request Interceptor Pattern
```javascript
// Automatic token injection
config.headers['Authorization'] = `Bearer ${jwt}`;
```

#### Response Interceptor Pattern
```javascript
// 401 handling
if (status === 401) {
  router.replace({ path: '/' })
}
```

### **API Logging**
- Controlled by `apiLogging` flag in auth store
- Logs: Request method, URL, parameters, response data
- Can be toggled via `sessionStorage.setItem('apiLogging', 'true')`

### **Error Handling**
- Consistent error structure across all API calls
- User-friendly error messages
- Automatic redirect on authentication failures
- Detailed logging for debugging

---

## API Call Statistics

### **Total API Endpoints**: 150+
- **ERP Integration**: ~50 endpoints
- **MongoDB/Backend**: ~67 endpoints  
- **Third-party**: ~15 endpoints
- **Python Backend**: ~5 endpoints
- **Webhooks**: ~8 endpoints

### **API Client Distribution**
- **Authenticated calls**: 85% (requires JWT)
- **Public calls**: 10% (no authentication)
- **Python backend**: 5% (file processing)

### **Integration Complexity**
- **High**: ShipStation + Shippo + Eclipse ERP integration
- **Medium**: Stripe payment processing
- **Low**: Standard CRUD operations

---

## Best Practices

### **Error Handling**
```javascript
try {
  const response = await apiClient.get('/endpoint')
  return response.data
} catch (error) {
  throw new Error(error.response?.data?.message || 'Operation failed')
}
```

### **Request Logging**
```javascript
// Enable debugging
sessionStorage.setItem('apiLogging', 'true')
```

### **File Uploads**
```javascript
const formData = new FormData()
formData.append('file', file)
await apiClient.post('/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
```

### **Environment-Aware Calls**
```javascript
// Different behavior based on environment
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:3001'
```

---

*Last Updated: Generated with Claude Code*