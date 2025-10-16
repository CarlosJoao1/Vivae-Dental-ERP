# Vivae Dental ERP – Technical Documentation

## Architecture
- **App Factory** pattern
- Blueprints per domain: `auth`, `masterdata`, `tenants`, `health`
- MongoEngine models: `User`, `Laboratory`
- JWT with access/refresh tokens; claims include `role` and `tenant_id`

## JWT Flow
1. `/api/auth/login` → returns `access_token` (30m), `refresh_token` (7d)
2. Frontend stores tokens (access in memory, refresh in httpOnly if applicable)
3. Use `Authorization: Bearer <access>` in API calls
4. When 401/expired, call `/api/auth/refresh` with refresh token

## Multi-Tenant
- Tenant = `Laboratory`
- Users reference `tenant_id`
- Future: per-tenant query scoping, roles per tenant

## Feature Licensing (stub)
- `core/license.py` exposes `LicenseManager`
- Decorator `@current_app.license.require("feature")` (to be wired in app)

## Data Model (initial)
### Laboratory
- name (unique), address, country, postal_code, city, tax_id, phone, email, active

### User
- username (unique), email, role, password_hash, tenant_id (ref Laboratory)

## API
- `/api` (root info), `/api/health`, `/api/health/info`
- `/api/auth/login`, `/api/auth/refresh`, `/api/auth/me`
- `/api/tenants`
- `/api/masterdata/laboratories` (list/create/update)
- stubs: patients, technicians, services, document-types

### Health & Versioning
- Endpoint: `GET /api/health/info`
	- Fields: `ok`, `version`, `branch`, `commit`, `build_time`
	- Version strategy: `APP_VERSION` env if set, otherwise `v[ISOYearWeek].01`
	- Datetime handling: timezone-aware (`datetime.now(timezone.utc)`) para cálculo de semana ISO

### Frontend Observability
- Topbar exibe badge de versão com tooltip (branch, short SHA, build time)
- Consumo de `/api/health/info` no mount

### Frontend Refactors
- Remoção de ternários e template literals aninhados em cálculos de encomendas e faturas
	- Helpers: `calcGross`, `calcDiscount`, `calcNet`
	- Mesma lógica, melhor legibilidade e conformidade com lints (S4624, S3358)

## Deployment Notes
- Set `SECRET_KEY` and `JWT_SECRET_KEY` via env
- Use Gunicorn behind reverse proxy (Nginx)
- Configure CORS per environment
- `APP_VERSION` opcional para controlar a versão exibida
- Render envs de build/runtime: `RENDER_GIT_BRANCH`, `RENDER_GIT_COMMIT`, `RENDER_BUILD_TIME`
