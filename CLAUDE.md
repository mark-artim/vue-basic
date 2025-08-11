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