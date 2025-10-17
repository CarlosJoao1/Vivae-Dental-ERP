# Changelog

All notable changes to this project will be documented in this file.

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
