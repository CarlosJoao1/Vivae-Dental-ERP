# Changelog

All notable changes to this project will be documented in this file.

## v0.3.0 - 2025-10-19 (Production Module Release)

### Production Module - Complete Implementation

**Backend (Phase B - Journals & Ledger Entries)**
- **New Models** (3 models, ~300 lines):
  - `ItemLedgerEntry`: Tracks material consumption and finished goods output with UUID posting_id for idempotency
  - `CapacityLedgerEntry`: Tracks work center/machine capacity usage (setup/run/stop times, operator tracking)
  - `ProductionJournal`: Journal headers for Consumption/Output/Capacity postings with reversal support
  
- **PostingService** (370 lines):
  - Idempotent posting logic: checks posting_id uniqueness before insert
  - Handles race conditions: returns success if posting already exists
  - Three posting methods: `post_consumption()`, `post_output()`, `post_capacity()`
  - Validation: item existence, quantity > 0, work center validation, production order existence
  
- **Journals API** (6 new endpoints):
  - `POST /api/production/journals/consumption`: Post material consumption with multi-item support
  - `POST /api/production/journals/output`: Post finished goods output
  - `POST /api/production/journals/capacity`: Post capacity usage (times + operator)
  - `GET /api/production/journals`: List journals with filters (type, order, date range)
  - `GET /api/production/journals/ledger/items`: Query item ledger entries
  - `GET /api/production/journals/ledger/capacity`: Query capacity ledger entries

**Frontend (Phase A - Department Pages)**
- **ProductionCapabilities.tsx** (326 lines):
  - Work Centers and Machine Centers management
  - Collapsible machine lists per work center
  - Capacity utilization charts with visual progress bars
  - Efficiency color coding: green ≥90%, yellow ≥75%, red <75%
  - Quick stats: Total WCs, Total Machines, Total Capacity, Avg Efficiency
  
- **ProductionPlanning.tsx** (286 lines):
  - Production Orders management with full workflow
  - Filter tabs by status with real-time counts
  - Release/Finish/Cancel workflow actions via API
  - Status-conditional buttons (Planned→Release, Released→Finish, both→Cancel)
  - MRP section placeholder for Phase C
  
- **ProductionExecution.tsx** (214 lines):
  - Shop Floor Dashboard with operations queue
  - Status-conditional action buttons (Ready→Start, In Progress→Pause/Complete)
  - Journal Posting section with Consumption/Output/Capacity buttons
  - Integration placeholders for Phase C journal modal
  
- **ProductionCosting.tsx** (simplified):
  - Cost analysis: Standard vs Actual with variance breakdown
  - Material/Labor/Overhead decomposition with visual charts
  - Percentage variance display
  
- **ProductionTasks.tsx** (simplified):
  - Operator task queue interface
  - Filter by status and work center
  - Priority indicators (High/Normal/Low) with color coding
  - Task assignment tracking

**Navigation & Infrastructure**
- Updated `Sidebar.tsx`: Added Costing and Tasks links to Production submenu
- Updated `App.tsx`: Added 4 new routes (Planning, Execution, Costing, Tasks)
- Updated `routes/__init__.py`: Registered journals blueprint at `/api/production/journals`

**Documentation**
- Updated `TECHNICAL_SPEC.md`: Complete Phase A + Phase B documentation
- 62 production endpoints total (existing + 6 new journals endpoints)
- Idempotency patterns and posting workflow documented

**Statistics**
- 13 commits on feature/production-navpp branch
- ~8,600 total lines (backend + frontend)
- 6 frontend pages complete
- 3 backend models + 1 service + 6 endpoints

**Next Phase (C - In Progress)**
- BOMForm.tsx: Dynamic line editing with react-hook-form
- RoutingForm.tsx: Dynamic operation editing
- ProductionOrderForm.tsx: Item selector with auto-load
- Journal posting modal integration in ProductionExecution

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
