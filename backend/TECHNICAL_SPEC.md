# Dental Lab ERP – Technical Spec (Backend)

Date: 2025-09-25

## Stack
- Flask 3 + Flask-JWT-Extended
- MongoDB via MongoEngine
- CORS enabled
- i18n JSON dictionaries

## Multi-Tenancy
- Root entity: Laboratory
- All other docs reference `lab`
- Scope derived from JWT identity (`lab_id`)

## Auth
- /api/auth/register
- /api/auth/login (returns access + refresh)
- /api/auth/refresh
- /api/auth/me

## Master Data Endpoints
- /api/masterdata/patients (GET, POST)
- /api/masterdata/technicians (GET, POST)
- /api/masterdata/services (GET, POST)
- /api/masterdata/document-types (GET, POST)

## Licensing
- `license.json` in project root
- Decorator: `@current_app.license.require('<feature>')`

## Configuration
- `.env` with MONGO_URI, JWT_SECRET, token expiries, DEFAULT_LANG

## Seed
- Vivae Dental Lab (PT) + admin user (admin/admin123)

## Roadmap
- Roles/permissions per endpoint
- Advanced audit logs
- File storage and external services
- Workflows (MES) and production tracking
