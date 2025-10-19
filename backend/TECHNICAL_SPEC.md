# Dental Lab ERP – Technical Spec (Backend)

Date: 2025-10-19 (Updated with Production Module)

## Stack
- Flask 3 + Flask-JWT-Extended
- SQLAlchemy 2.0 + PostgreSQL
- CORS enabled
- i18n JSON dictionaries (pt, en, es, fr, zh)

## Multi-Tenancy
- Root entity: Laboratory
- All models include `tenant_id` field
- Scope derived from JWT token (`tenant_id`)

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

## Production Module (Complete)

### Master Data
- **Items (Services)**: Raw materials, semi-finished, finished goods
- **UOMs**: Units of measure with conversion factors
- **Work Centers**: Production departments with capacity/efficiency
- **Machine Centers**: Individual machines within work centers

### Design & Engineering (62 endpoints total)
- **BOMs (Bill of Materials)**:
  - CRUD operations with dynamic lines
  - BOM Explosion algorithm (recursive, multi-level)
  - Versioning system (New → Under Development → Certified)
  - Component types: Item or Resource
  - Scrap percentage tracking
  
- **Routings**:
  - CRUD operations with dynamic operations
  - Time calculation (setup + run per quantity)
  - Work center and machine center assignment
  - Concurrent capacities support
  - Operation sequencing

### Planning
- **Production Orders**:
  - Create from item + quantity + due date
  - Auto-load certified BOM/Routing versions
  - Status workflow: Planned → Released → In Progress → Finished → Closed
  - Release/Finish/Cancel actions via API

### Journals & Ledger Entries (Phase B - NEW)
- **ItemLedgerEntry Model**:
  - Tracks material consumption and finished goods output
  - Fields: posting_id (UUID), item_no, quantity (+ for output, - for consumption), entry_type, production_order_no, work_center_code
  - Indexed by tenant_id + item_no, posting_id, production_order_no
  
- **CapacityLedgerEntry Model**:
  - Tracks work center/machine capacity usage
  - Fields: posting_id (UUID), work_center_code, machine_center_code, setup_time, run_time, stop_time, scrap_time, operator_id
  - Indexed by tenant_id + work_center_code, posting_id, production_order_no
  
- **ProductionJournal Model**:
  - Journal headers for all postings
  - Fields: posting_id (UUID), journal_type (Consumption/Output/Capacity), production_order_no, posted_by, status
  - Support for reversal tracking
  
- **PostingService (370 lines)**:
  - Idempotent posting logic (checks posting_id uniqueness)
  - Validation: item exists, quantity > 0, work center exists, etc.
  - Handles race conditions (IntegrityError returns success)
  - Three posting types: post_consumption(), post_output(), post_capacity()

### Journals API Endpoints (6 new endpoints)
- POST /api/production/journals/consumption
  - Body: {posting_id, production_order_no, items: [{item_no, quantity, uom_code}], work_center_code, operation_no}
  - Creates journal + multiple ItemLedgerEntry records
  - Returns: {success, posting_id, entries_created, message, already_posted}
  
- POST /api/production/journals/output
  - Body: {posting_id, production_order_no, item_no, quantity, uom_code, work_center_code}
  - Creates journal + ItemLedgerEntry (positive quantity)
  
- POST /api/production/journals/capacity
  - Body: {posting_id, production_order_no, operation_no, work_center_code, setup_time, run_time, operator_id}
  - Creates journal + CapacityLedgerEntry
  
- GET /api/production/journals
  - Query: journal_type, production_order_no, from_date, to_date, limit, offset
  - Returns paginated list of journal headers
  
- GET /api/production/journals/ledger/items
  - Query: item_no, entry_type, production_order_no, from_date, to_date
  - Returns ItemLedgerEntry records with filters
  
- GET /api/production/journals/ledger/capacity
  - Query: work_center_code, machine_center_code, operator_id, production_order_no
  - Returns CapacityLedgerEntry records with filters

### Frontend Pages (Phase A - Complete)
1. **ProductionDesign.tsx** (268 lines):
   - BOMs and Routings list with status badges
   - BOM Explosion and Time Calculation buttons
   - Quick stats: Certified BOMs/Routings, In Development count
   
2. **ProductionCapabilities.tsx** (326 lines):
   - Work Centers and Machine Centers management
   - Collapsible machine lists per work center
   - Capacity utilization charts
   - Efficiency color coding (green ≥90%, yellow ≥75%, red <75%)
   
3. **ProductionPlanning.tsx** (286 lines):
   - Production Orders with filter tabs
   - Release/Finish/Cancel workflow buttons
   - Status-conditional actions
   - MRP placeholder section
   
4. **ProductionExecution.tsx** (214 lines):
   - Shop Floor Dashboard with operations queue
   - Status-conditional buttons (Start/Pause/Complete)
   - Journal Posting section (placeholders for Phase B integration)
   
5. **ProductionCosting.tsx** (simplified):
   - Cost breakdown: Material/Labor/Overhead
   - Standard vs Actual variance analysis
   - Visual charts with progress bars
   
6. **ProductionTasks.tsx** (simplified):
   - Operator task queue interface
   - Filter by status and work center
   - Task assignment tracking

## Licensing
- `license.json` in project root
- Module flags: `"producao": true` (valid until 2027-12-31)
- Decorator: `@license_required('producao')`

## Configuration
- `.env` with DATABASE_URL, JWT_SECRET, token expiries, DEFAULT_LANG
- PostgreSQL connection via SQLAlchemy

## Seed Data
- Vivae Dental Lab (PT) + admin user (admin/admin123)
- Production seed: 5 items, 3 UOMs, 2 work centers, 3 machines, 1 BOM, 1 routing, 2 production orders

## Phase C Roadmap (In Progress)
- BOMForm.tsx: Dynamic line editing with react-hook-form
- RoutingForm.tsx: Dynamic operation editing
- ProductionOrderForm.tsx: Item selector with auto-load BOM/Routing
- JournalPostingModal.tsx: Multi-tab form for Consumption/Output/Capacity
- Integration: Replace all alert() placeholders with actual forms

## Future Enhancements
- MRP (Material Requirements Planning)
- Advanced scheduling with capacity constraints
- Real-time shop floor monitoring
- Cost rollup automation
- Integration with Inventory module
