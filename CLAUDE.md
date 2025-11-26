# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Commands

### Development
- `npm run dev` - Start development server on port 3000 (Vue 3 + Vuetify frontend)
- `npm run build` - Build frontend for production
- `npm run lint` - Lint and fix JavaScript/Vue files with ESLint

### Backend Services
- `cd auth-backend && npm start` - Start Node.js authentication backend (Express + MongoDB)
- `cd backend && python main.py` - Start Python backend for data processing (Flask)

## Architecture Overview

This is a multi-tier application with:

### Frontend (Vue 3 + Vuetify)
- **Framework**: Vue 3 with Composition API, Vuetify 3 for UI components
- **Build Tool**: Vite with custom configuration for Vuetify auto-imports
- **State Management**: Pinia stores for auth, menu, and other state
- **Routing**: Vue Router with authentication guards (`requiresAuth` meta)
- **Key Directories**:
  - `src/pages/` - Main application pages, includes admin subdirectory
  - `src/stores/` - Pinia state stores (auth.js for JWT auth)
  - `src/api/` - API client modules for different endpoints
  - `src/utils/` - Utility functions including axios configuration

### Authentication Backend (Node.js/Express)
- **Location**: `auth-backend/` directory
- **Database**: MongoDB with Mongoose ODM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Key Features**: User management, company management, logging infrastructure
- **Controllers**: Organized by feature (user, product, email, etc.)

### Python Backend (Flask)
- **Location**: `backend/` directory
- **Purpose**: Data processing and file comparison utilities
- **Key Files**: `main.py` (entry point), `compare_invbal.py` (inventory comparison)

### Django Backend
- **Location**: `django-backend/` directory
- **Purpose**: Product-specific tools and features (PDW Data Prep, Product Merge, etc.)
- **Database**: Uses same MongoDB as Node.js backend
- **Authentication**: Session-based with product authorization framework
- **UI**: Tailwind CSS (no Bootstrap)

## EMP54 Data and User Access Flow

**CRITICAL**: These principles define the core business logic of the EMP54 platform and must be adhered to in all implementations.

### Business Model
- **Our Company**: emp54 - the software platform provider
- **Our Customers**: Companies that subscribe to our products
- **Users**: Employees of customer companies who access the platform

### Data Hierarchy
```
emp54 (our company)
└── Company (customer company)
    ├── Users (company employees)
    │   ├── Admin User(s) - at least one required per company
    │   └── Regular Users
    └── Product Subscriptions
        └── Products (individual features/tools)
```

### Product Access Rules
1. **Company Subscriptions**: Companies purchase subscriptions to products
2. **Product Availability**: When a company is subscribed to a product:
   - It becomes available as an option for company admin user(s) to manage
   - It becomes a valid option for non-admin users to be assigned access
3. **User Access Assignment**: Users are assigned access to specific products that their company subscribes to
4. **Menu Visibility**: When a user is assigned access to a product, the menus/features associated with that product appear in their navigation

### User Types and Authentication
1. **Admin Users** (EMP54 Staff):
   - Authenticate against MongoDB using bcrypt password hashing
   - Have userType = 'admin' in MongoDB
   - Do NOT authenticate against company ERP systems
   - Have full access to all products (no authorization checks)

2. **Customer Users** (Company Employees):
   - Authenticate against their company's ERP system
   - Password verification happens at ERP, not MongoDB
   - Must have product authorization to access features
   - Product access controlled by company subscriptions + user assignments

### Logging Requirements
- **Login Attempts**: All successful and failed login attempts MUST be logged
- **Existing Infrastructure**: Use the existing logging infrastructure (logService in Node.js, logging in Django)
- **Log Data Should Include**:
  - User ID and email
  - Company ID and company code
  - Timestamp
  - Success/failure status
  - IP address (if available)
  - Authentication method (ERP vs MongoDB)

### Implementation Guidelines
- Product authorization enforced via `@require_product()` decorator in Django
- Product authorization middleware checks all routes automatically
- User product access stored in MongoDB user document as `products` array
- Company product subscriptions checked before allowing user assignment
- Menu rendering based on user's authorized products list

## Key Architectural Patterns

### Authentication Flow
- JWT tokens stored in localStorage and auth store
- Router guards check `authStore.isAuthenticated` before protected routes
- Axios interceptors handle token attachment and refresh

### API Communication
- `axiosPublic.js` for unauthenticated requests
- `axios.js` for authenticated requests with JWT header injection
- Port-based environment switching (5000=Production, 5001=Train, etc.)

### Component Organization
- Pages in `src/pages/` with admin pages in subdirectory
- Reusable components in `src/components/`
- Layout system using `src/layouts/MainLayout.vue`

### State Management
- Pinia stores with Composition API pattern
- Auth store manages user session, ports, and API configuration
- Menu store handles dynamic navigation based on user permissions

## Development Notes

### File Extensions
The Vite config supports `.js`, `.vue`, `.ts`, `.tsx` extensions with `@` alias pointing to `src/`.

### Styling
- Vuetify theme configuration in `src/plugins/vuetify.js`
- Custom SCSS settings in `src/styles/settings.scss`
- Roboto font auto-imported via unplugin-fonts

### Backend Dependencies
- Node.js backend requires MongoDB connection
- Python backend uses pandas for data processing
- Multiple bat files for starting all services simultaneously

## Server Management Best Practices

### Process Management for Node.js Backend (Port 3001)
**CRITICAL**: This project is prone to multiple Node.js processes running simultaneously on port 3001, which causes:
- 404 errors on new API endpoints
- Old code running despite file changes
- Routing conflicts and unpredictable behavior

### Before Starting Backend Server:
1. **Always check for existing processes on port 3001:**
   ```bash
   netstat -ano | findstr :3001
   ```

2. **Kill all existing Node.js processes on port 3001:**
   ```bash
   # Note the PID from netstat output, then use PowerShell (taskkill has path issues in Git Bash):
   powershell "Stop-Process -Id <PID_NUMBER> -Force"
   ```

3. **Verify port is free before starting:**
   ```bash
   netstat -ano | findstr :3001
   # Should return no results
   ```

4. **Start server cleanly:**
   ```bash
   cd auth-backend && npm start
   ```

### When Code Changes Don't Take Effect:
- **Problem**: Server running old cached code
- **Solution**: Kill all Node.js processes and restart cleanly
- **Symptoms**: API returns old error messages, new routes return 404, database queries use old schema paths

### Background Process Management:
- Use `run_in_background: true` for long-running servers
- Track background process IDs for proper cleanup
- Kill old background processes before starting new ones
- Use BashOutput tool to monitor server startup and confirm route mounting

### Database Schema Considerations:
- Company Shippo token stored at: `company.ship54Settings.shippo.customerToken.encrypted`
- NOT at: `company.shippoToken` (this path doesn't exist)
- Always verify database schema paths when adding new API endpoints

## Critical Process Management Lessons

### The "Impossible" Scenario - Code Changes Not Taking Effect
**What happened**: Even after:
- Updating code files (shipping.js, shipments.js)
- Seeing "server restarted" messages
- Confirming routes are mounted
- Multiple restart attempts

**The API still returned old error messages** ("Company Shippo token not configured")

**Root Cause**: Ghost processes persist even when you think they're killed
- Process PID 47096 remained active and handling requests
- New processes started but couldn't bind to port 3001
- `netstat` showed the old PID still listening on the port
- Background process output showed route mounting but server wasn't actually handling requests

### The Definitive Process Kill Strategy:
1. **Never trust a single kill attempt** - processes can survive
2. **Always verify with netstat** after killing:
   ```bash
   netstat -ano | findstr :3001
   # Should show NO listening processes, only TIME_WAIT connections
   ```
3. **Use PowerShell for reliable process killing**:
   ```bash
   powershell "Stop-Process -Id <PID> -Force"
   ```
4. **Test API connectivity** after restart:
   ```bash
   curl -X GET "http://localhost:3001/api/test-route"
   # Should return JSON response, not connection errors
   ```
5. **Kill ALL background bash processes** if in doubt:
   ```bash
   # Use KillBash tool for each background process ID
   ```

### Warning Signs of Ghost Processes:
- API responses don't match recent code changes
- New endpoints return 404 despite route mounting logs
- Database schema paths fail despite correct code
- Server appears to start but curl requests fail
- netstat shows unexpected PID handling the port

### Emergency Reset Procedure:
When nothing else works:
1. Kill all Node.js processes: `powershell "Get-Process node | Stop-Process -Force"`
2. Verify port is free: `netstat -ano | findstr :3001`
3. Kill all background bash processes via KillBash tool
4. Start fresh server with new background process
5. Confirm with curl test before proceeding