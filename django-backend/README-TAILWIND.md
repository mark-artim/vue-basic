# Tailwind CSS Setup - Django Backend

## Overview
This Django backend uses **Tailwind CSS v4** with the CLI for production-ready builds.

## Development

### Build CSS Once
```bash
npm run build:css
```

### Watch for Changes (during development)
```bash
npm run watch:css
```
This will rebuild CSS automatically when you modify templates.

### Start Django Server
The `dev-menu.bat` automatically builds CSS before starting Django:
```bash
npm run build:css && python manage.py runserver
```

## Files

### Input CSS
- `static/css/input.css` - Your custom Tailwind config and utilities

### Output CSS
- `static/css/output.css` - Generated, minified CSS (DO NOT EDIT)
- This file is **gitignored** and regenerated on each build

### Templates
- `templates/base_tailwind.html` - Base template with nav
- `templates/home_tailwind.html` - Product cards homepage
- `templates/customer_auth/login_tailwind.html` - Customer login
- `templates/adminportal/login_tailwind.html` - Admin login

## Custom Classes

### Glass Effect
```html
<div class="glass-effect">...</div>
```

### Nav Gradient
```html
<nav class="nav-gradient">...</nav>
```

### Nav Link Hover
```html
<a class="nav-link-hover">Link</a>
```

## Deployment (Railway)

Railway will automatically:
1. Install npm dependencies (`tailwindcss`, `@tailwindcss/cli`)
2. Run `npm run build:css` (if configured in build command)
3. Start Django

### Railway Build Command
```bash
npm install && npm run build:css && pip install -r requirements.txt
```

### Railway Start Command
```bash
python manage.py runserver 0.0.0.0:$PORT
```

## Theme Colors

Custom colors defined in `input.css`:
- `--color-primary`: #1976d2 (Blue - matches Vuetify)
- `--color-secondary`: #424242 (Dark gray)
- `--color-accent`: #82b1ff (Light blue)

## Fonts

- **Inter** - Google Fonts (Sanity.io style)
- Fallback: ui-sans-serif, system-ui

## Tips

1. **Development**: Use `npm run watch:css` in a separate terminal while coding
2. **Production**: `npm run build:css` minifies CSS
3. **New utilities**: Add to `input.css` and rebuild
4. **Debugging**: Check `static/css/output.css` to see compiled CSS
