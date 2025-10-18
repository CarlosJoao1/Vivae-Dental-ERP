# Changelog

All notable changes to this project will be documented in this file.

## v0.2.1 - 2025-10-18

Backend
- CORS: allow custom header `X-Tenant-Id` to support tenant override from the frontend across all routes. Fixes preflight failures that caused Axios Network Error and timeouts.
- Auth: `/api/auth/me` now returns resolved permissions for the active tenant (sysadmin → all permissions; otherwise role-based from RolePolicy).
- Auth: new `/api/auth/stats` endpoint returns tenants count accessible by the user and active users count within current lab; total users for sysadmin.
- Tenancy: uniform `X-Tenant-Id` support in masterdata and sales route helpers with permission checks (sysadmin bypass or header in allowed_labs).

Frontend
- Topbar: Diagnostics panel to test `/health`, `/health/info`, `/health/deep`; status dot shows API/DB connectivity.
- Permissions: Permissions tab visible to Admin and Sysadmin; reads permissions from `/auth/me`.
- Dashboard: fixed tenants count and added active users metric via `/auth/stats`; auto-reloads metrics on tenant changes.

Reliability
- Render cold start resilience: automatic single retry on network/timeout.

Versioning
- Backend health/info exposes computed version `vYYYYWW.01` or `APP_VERSION` if set.

## v0.2.0 - 2025-10-17

Frontend
- Clients: added fields postal_code, country_code (select, uppercase), default_shipping_address (select), location_code, and name in the modal; create/edit with inline error banners.
- Master Data UI: Countries and Shipping Addresses tabs show backend validation errors inline.

Backend
- Referential integrity and validations:
  - Prevent changing/deleting Country code when referenced by clients/shipping addresses.
  - Validate country_code existence and normalize uppercase for clients/shipping addresses.
  - Validate default_shipping_address exists within the lab for clients.

Reliability & UX
- SPA deep-link production fix, i18n parity gate at build, SMTP diagnostics and timeouts, version surfaced in Topbar via /api/health/info.

Versioning
- Git tag: v0.2.0
- Frontend package.json bumped to 0.2.0
