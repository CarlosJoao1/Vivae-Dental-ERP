# Vivae Dental ERP – Technical Documentation

This document provides a structured overview of the system’s architecture, APIs, frontend, i18n, deployment, and operational practices.

## Table of Contents
- Architecture overview
- Backend
	- Data model
	- Auth & JWT flow
	- Multitenancy
	- Health & versioning
	- API endpoints
- Frontend
	- Structure & routing
	- Observability (version badge)
	- i18n (localization)
	- Notable refactors
- Configuration & Environment
- Deployment
- Quality gates
- Troubleshooting

## Architecture overview
- Flask app using the App Factory pattern
- Blueprints per domain: `auth`, `masterdata`, `tenants`, `health`
- MongoEngine ODM models
- JWT-based authentication (access/refresh)
- React + Vite + TypeScript frontend with Tailwind CSS and i18next

## Backend

### Data model (initial)
- Laboratory: name (unique), address, country, postal_code, city, tax_id, phone, email, active
- User: username (unique), email, role, password_hash, tenant_id (ref Laboratory)

### Auth & JWT flow
1. `/api/auth/login` → returns `access_token` (~30m) and `refresh_token` (~7d)
2. Frontend stores tokens (access in memory/localStorage; refresh managed by app logic)
3. API calls use `Authorization: Bearer <access>`
4. On 401/expiry, call `/api/auth/refresh` with refresh token, queueing requests client-side

### Multitenancy
- Tenant = `Laboratory`; users reference `tenant_id`
- Future work: per-tenant query scoping and roles per tenant

### Health & versioning
- Endpoint: `GET /api/health/info`
	- Fields: `ok`, `version`, `branch`, `commit`, `build_time`
	- Version strategy: `APP_VERSION` env overrides; default `v[ISOYearWeek].01`
	- Timezone-aware ISO week computation: `datetime.now(timezone.utc)`

### API endpoints
- Root: `/api` (meta), `/api/health`, `/api/health/info`
- Auth: `/api/auth/login`, `/api/auth/refresh`, `/api/auth/me`
- Tenants: `/api/tenants`
- Masterdata: `/api/masterdata/laboratories` (list/create/update)
- Planned: patients, technicians, services, document-types

## Frontend

### Structure & routing
- React 18 + Vite, TypeScript, Tailwind
- Authenticated routes, Topbar, Sidebar, Dashboard layout

### Observability (version badge)
- Topbar fetches `/api/health/info` on mount
- Displays `version` with tooltip: `branch`, short `commit` SHA, `build_time`

### i18n (localization)
- i18next setup at `src/i18n/index.ts`
- Locales: `pt`, `en`, `es`, `fr`, `cn`, `de` under `src/i18n/locales/*/common.json`
- Added/ensured keys: `discount`, `global_discount`, `line_discount`, `subtotal`, `subtotal_after_discount`, `tax`, `grand_total`, `print`, `save_pdf`

### Notable refactors
- Removed nested ternaries/template literals in order/invoice calculations
- Introduced helpers: `calcGross`, `calcDiscount`, `calcNet`
- Improves readability and lint adherence (S4624, S3358)

## Configuration & Environment
- Backend env vars:
	- `SECRET_KEY` (required in production)
	- `JWT_SECRET_KEY` (required; falls back to `SECRET_KEY` with a warning if absent)
	- `APP_VERSION` (optional) to override default versioning
	- `FRONTEND_ORIGINS` (CORS)
	- `MONGO_URI`
- Frontend env vars:
	- `VITE_API_BASE` (preferred) or `VITE_API_BASE_URL`
- Dev: `.env.example` provided for both backend and frontend

## Deployment
- Render blueprint (`render.yaml`), backend (web) + frontend (static)
- SPA rewrites configured for the static site
- Health endpoints for diagnostics
- Build/runtime vars exposed by Render: `RENDER_GIT_BRANCH`, `RENDER_GIT_COMMIT`, `RENDER_BUILD_TIME`

## Quality gates
- Lint/Typecheck: TypeScript (frontend) and Python
- Tests: none yet; recommend adding unit tests for pricing/discount calculations
- Security: enforce secrets in production; JWT keys must be set

## Troubleshooting
- Backend fails to start (prod): ensure `SECRET_KEY` and `JWT_SECRET_KEY` are set
- JWT warnings: set `JWT_SECRET_KEY` different from `SECRET_KEY` to remove fallback warning
- CORS errors: validate `FRONTEND_ORIGINS` includes deployed frontend URL
- Version badge empty: backend `/api/health/info` reachable? `APP_VERSION` set?
