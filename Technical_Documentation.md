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
- Active tenant resolution on backend:
	- Default: `tenant_id` from JWT.
	- Override via header `X-Tenant-Id` if the user has permission:
		- Sysadmin: may access any tenant.
		- Non-sysadmin: only if `X-Tenant-Id` is contained in `allowed_labs` of the user.
- Frontend always attaches `X-Tenant-Id` when a tenant is selected in the Topbar selector.
- CORS: backend allows `X-Tenant-Id` in `Access-Control-Allow-Headers`.

### Permissions & Roles
- Model: `RolePolicy` persiste um dicionário de permissões por laboratório e por role.
- `/api/auth/me`: devolve o utilizador autenticado e `permissions` resolvidas para o tenant ativo.
	- Sysadmin ⇒ `{ "__role__": "sysadmin", "all": true }`.
	- Caso contrário ⇒ política efetiva proveniente de `RolePolicy`.
- UI: a aba de Permissões (Master Data) é visível para Sysadmin e Admin.
- Enforcement (em progresso): helpers backend para verificar `can(user, lab, feature, action)` nos endpoints.

### Health & versioning

### Health & versioning
- Endpoint: `GET /api/health/info`
	- Fields: `ok`, `version`, `branch`, `commit`, `build_time`
	- Version strategy: `APP_VERSION` env overrides; default `v[ISOYearWeek].01`
	- Timezone-aware ISO week computation: `datetime.now(timezone.utc)`

### API endpoints
- Root: `/api` (meta), `/api/health`, `/api/health/info`
- Auth: `/api/auth/login`, `/api/auth/refresh`, `/api/auth/me`
- Auth (stats): `/api/auth/stats` → métricas rápidas para Dashboard
	- `tenants_accessible` (número de tenants visíveis para o utilizador)
	- `users_in_tenant` (contagem de utilizadores no tenant ativo; inclui `tenant_id` ou `allowed_labs`)
	- `total_users` (apenas para sysadmin)
- Tenants: `/api/tenants`
- Masterdata: `/api/masterdata/laboratories` (list/create/update)
- Planned: patients, technicians, services, document-types

## Frontend

### Structure & routing
- React 18 + Vite, TypeScript, Tailwind
- Authenticated routes, Topbar, Sidebar, Dashboard layout

### Tenant header propagation
- Axios interceptor (`src/api/api.ts`) adiciona `Authorization` e `X-Tenant-Id` (se existir) a todas as requests.
- Em dev, baseURL usa `VITE_API_BASE`/`VITE_API_BASE_URL` ou `http://localhost:5000/api` por omissão.
- Timeout: 20s em dev; 60s em produção (Render cold start).

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

### Permissions panel (UI)
- Visível para roles: Sysadmin e Admin.
- Lê permissões através de `/api/auth/me` para gating de UI.
- O Dashboard usa `/api/auth/stats` para mostrar número de tenants e utilizadores ativos no tenant corrente.

## Configuration & Environment
- Backend env vars:
	- `SECRET_KEY` (required in production)
	- `JWT_SECRET_KEY` (required; falls back to `SECRET_KEY` with a warning if absent)
	- `APP_VERSION` (optional) to override default versioning
	- `FRONTEND_ORIGINS` (CORS exact matches)
	- `FRONTEND_ORIGINS_EXTRA` (CORS wildcard patterns, e.g., `https://vivae-dental-erp-*.onrender.com`)
	- Nota: deve permitir a origem do frontend (ex.: `https://<frontend>.onrender.com`) e locais de dev.
	- `MONGO_URI`
- Frontend env vars:
	- `VITE_API_BASE` (preferred) or `VITE_API_BASE_URL`
	- Em Render (static), prefira configurar `VITE_API_BASE` "From Service" → backend web; evite hardcode no `.env.production`.
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
	- Se o frontend usar subdomínios efémeros (xyz.onrender.com), configure `FRONTEND_ORIGINS_EXTRA` com um wildcard.
- Preflight bloqueado com `X-Tenant-Id`:
	- Verifique que o backend expõe `Access-Control-Allow-Headers: Content-Type, Authorization, X-Tenant-Id`.
	- Se necessário, reinicie o container/backend e faça Hard Refresh no navegador.
- Version badge empty: backend `/api/health/info` reachable? `APP_VERSION` set?
