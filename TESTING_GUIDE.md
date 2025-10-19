# 🧪 Manual Testing Guide - Master Data Forms & Production Order Details

## Test Date: October 20, 2025
## Branch: feature/production-navpp
## Commit: 54a48b5

---

## ✅ Pre-requisites

1. **Docker containers running**: ✓
   ```bash
   docker-compose ps
   # backend: http://localhost:5000
   # frontend: http://localhost:5173
   # mongo: localhost:27017
   ```

2. **Login credentials**:
   - Navigate to: http://localhost:5173
   - Login with test user credentials
   - Ensure JWT token is valid

3. **Seed data loaded**:
   ```bash
   docker-compose exec backend python -c "from core.seed import seed_production_data; seed_production_data()"
   ```

---

## 📋 Test Plan

### **Test 1: Master Data - Items Tab**

#### 1.1 View Items List
- [ ] Navigate to `/production/masterdata`
- [ ] Click on **Items** tab (should be active by default)
- [ ] Verify table displays with columns:
  - Item No.
  - Description
  - Type
  - Base UOM
  - Lead Time
  - Status
  - Actions (Edit/Delete)
- [ ] Verify search bar is visible and functional
- [ ] Expected: See 15 seed items (CROWN-001, BRIDGE-001, etc.)

#### 1.2 Create New Item
- [ ] Click **"➕ Create New"** button
- [ ] Verify modal opens with title: **"➕ Create Item"**
- [ ] **Test validation errors**:
  - [ ] Leave Item No. empty → Click Create → Should show "Item number is required"
  - [ ] Enter lowercase "item-001" → Should show "Use uppercase letters, numbers, hyphens and underscores only"
  - [ ] Leave Description empty → Should show "Description is required"
  - [ ] Enter negative Lead Time → Should show "Must be 0 or greater"

- [ ] **Create valid item**:
  - Item No: `TEST-ITEM-001`
  - Description: `Test Dental Crown`
  - Description 2: `Premium ceramic material`
  - Item Type: `Manufactured`
  - Base UOM: `PCS`
  - Lead Time: `5` days
  - Unit Cost: `150.50`
  - Status: `Active`
  - [ ] Click **"➕ Create"**
  - [ ] Verify toast notification: **"✅ Item created successfully!"**
  - [ ] Verify modal closes automatically
  - [ ] Verify new item appears in table

#### 1.3 Edit Existing Item
- [ ] Click **"✏️"** button on TEST-ITEM-001
- [ ] Verify modal opens with title: **"✏️ Edit Item"**
- [ ] Verify Item No. field is **disabled** (cannot change primary key)
- [ ] Change Description to: `Test Dental Crown - Updated`
- [ ] Change Unit Cost to: `175.00`
- [ ] Click **"💾 Update"**
- [ ] Verify toast: **"✅ Item updated successfully!"**
- [ ] Verify changes reflected in table

#### 1.4 Delete Item
- [ ] Click **"🗑️"** button on TEST-ITEM-001
- [ ] Verify native confirm dialog appears: "Are you sure you want to delete TEST-ITEM-001? This action cannot be undone."
- [ ] Click **Cancel** → Verify nothing happens
- [ ] Click **"🗑️"** again → Click **OK**
- [ ] Verify toast: **"✅ TEST-ITEM-001 deleted successfully!"**
- [ ] Verify item removed from table

#### 1.5 Search Functionality
- [ ] Type "CROWN" in search box
- [ ] Verify only items with "CROWN" in Item No. or Description are shown
- [ ] Clear search → Verify all items return

---

### **Test 2: Master Data - UOMs Tab**

#### 2.1 View UOMs List
- [ ] Click **"UOMs"** tab
- [ ] Verify table displays with columns:
  - Code
  - Description
  - Decimals
  - Actions
- [ ] Expected: See 5 seed UOMs (PCS, UNIT, KG, METER, GRAM)

#### 2.2 Create New UOM
- [ ] Click **"➕ Create New"**
- [ ] Verify modal opens (smaller, max-w-md)
- [ ] **Test validation**:
  - [ ] Enter lowercase "pcs" → Should show "Use uppercase letters and numbers only"
  - [ ] Enter more than 10 characters → Should show "Maximum 10 characters"

- [ ] **Create valid UOM**:
  - Code: `BOX`
  - Description: `Box of Items`
  - Decimals: `0` (whole numbers only)
  - [ ] Click **"➕ Create"**
  - [ ] Verify toast: **"✅ UOM created successfully!"**
  - [ ] Verify BOX appears in table

#### 2.3 Edit UOM
- [ ] Click **"✏️"** on BOX
- [ ] Verify Code field is disabled
- [ ] Change Description to: `Box Container`
- [ ] Change Decimals to: `2`
- [ ] Click **"💾 Update"**
- [ ] Verify toast: **"✅ UOM updated successfully!"**

#### 2.4 Delete UOM
- [ ] Click **"🗑️"** on BOX
- [ ] Confirm deletion
- [ ] Verify toast: **"✅ BOX deleted successfully!"**
- [ ] Note: If UOM is used by items, backend should return error

---

### **Test 3: Master Data - Locations Tab**

#### 3.1 View Locations List
- [ ] Click **"Locations"** tab
- [ ] Verify table displays:
  - Code
  - Name
  - City
  - Default (Yes/No)
  - Status (Active/Blocked)
  - Actions
- [ ] Expected: See 1 seed location (MAIN)

#### 3.2 Create New Location
- [ ] Click **"➕ Create New"**
- [ ] Verify larger modal (max-w-2xl) with organized layout
- [ ] **Create valid location**:
  - Code: `WAREHOUSE-02`
  - Name: `Secondary Warehouse`
  - Address: `456 Industrial Road`
  - City: `Porto`
  - Postal Code: `4000-001`
  - Country: `Portugal`
  - [ ] Check **"⭐ Set as default location"**
  - [ ] Leave **"🚫 Block"** unchecked
  - [ ] Click **"➕ Create"**
  - [ ] Verify toast: **"✅ Location created successfully!"**

#### 3.3 Edit Location
- [ ] Click **"✏️"** on WAREHOUSE-02
- [ ] Change City to: `Vila Nova de Gaia`
- [ ] Uncheck "Set as default"
- [ ] Check "Block this location"
- [ ] Click **"💾 Update"**
- [ ] Verify changes reflected

#### 3.4 Verify Info Box
- [ ] Open any location form
- [ ] Verify blue info box at bottom with tooltip about default/blocked locations

---

### **Test 4: Master Data - Suppliers Tab**

#### 4.1 View Suppliers List
- [ ] Click **"Suppliers"** tab
- [ ] Verify table displays:
  - Supplier ID
  - Name
  - Contact Info (email/phone)
  - Lead Time
  - Status
  - Actions
- [ ] Expected: See 1 seed supplier (SUP-DENTAL-MATERIALS-001)

#### 4.2 Create New Supplier
- [ ] Click **"➕ Create New"**
- [ ] Verify large modal (max-w-3xl) with 4 sections:
  - 📋 Basic Information
  - 📞 Contact Information
  - 📍 Address
  - 💼 Business Terms

- [ ] **Test email validation**:
  - [ ] Enter invalid email "test@invalid" → Should show "Invalid email address"

- [ ] **Create valid supplier**:
  - **Basic Information**:
    - Supplier ID: `SUP-TEST-001`
    - Name: `Test Medical Supplies Ltd`
  
  - **Contact Information**:
    - Contact Name: `João Silva`
    - Phone: `+351 912 345 678`
    - Email: `joao@testmedical.com`
  
  - **Address**:
    - Address: `Rua da Saúde, 123`
    - City: `Lisboa`
    - Postal Code: `1000-100`
    - Country: `Portugal`
  
  - **Business Terms**:
    - Lead Time: `14` days
    - Currency: `EUR (€)`
    - Payment Terms: `Net 30 days`
    - Status: `Active`
  
  - [ ] Click **"➕ Create"**
  - [ ] Verify toast: **"✅ Supplier created successfully!"**

#### 4.3 Edit Supplier
- [ ] Click **"✏️"** on SUP-TEST-001
- [ ] Verify Supplier ID is disabled
- [ ] Change Lead Time to: `10`
- [ ] Change Status to: `Inactive`
- [ ] Click **"💾 Update"**
- [ ] Verify changes reflected

---

### **Test 5: Production Order Details Modal**

#### 5.1 Navigate to Production Planning
- [ ] Navigate to `/production/planning`
- [ ] Verify production orders list is displayed
- [ ] Expected: See multiple orders with different statuses

#### 5.2 Open Order Details
- [ ] Click **"👁️ View"** button on any production order
- [ ] Verify modal opens (max-w-6xl, full screen height)
- [ ] Verify header shows:
  - Order number (e.g., "📦 PO-202510-ABC123")
  - Status badge with color
  - Item info: Item No. - Description
  - Summary line: Location | Quantity | Due Date

#### 5.3 Test General Tab
- [ ] Verify **"📋 General"** tab is active by default
- [ ] Verify sections displayed:
  - **Order Information**: Order No., Status, Priority
  - **📦 Item Information**: Item No., Description, Quantity, Location
  - **📅 Dates**: Start Date, Due Date
  - **🔧 Configuration**: BOM Version, Routing Version
  - **📝 Description**: (if available)
- [ ] Verify all fields are read-only (display mode)
- [ ] Verify dates are formatted correctly (MMM DD, YYYY)

#### 5.4 Test Lines Tab
- [ ] Click **"📝 Lines"** tab
- [ ] Verify badge shows line count (e.g., "3")
- [ ] If lines exist:
  - [ ] Verify table with columns: Line, Item No., Description, Quantity, Unit Cost, Total
  - [ ] Verify costs are formatted as currency (€)
  - [ ] Verify hover effect on rows
- [ ] If no lines:
  - [ ] Verify empty state: "📭 No lines found for this production order"

#### 5.5 Test Routing Tab
- [ ] Click **"🔄 Routing"** tab
- [ ] Verify badge shows operation count
- [ ] If operations exist:
  - [ ] Verify cards display for each operation:
    - Operation number and description
    - Work Center code
    - Status badge (color-coded)
    - Setup Time (⏱️) and Run Time (🏃)
  - [ ] Verify operations are in order
- [ ] If no operations:
  - [ ] Verify empty state: "🔄 No routing operations found"

#### 5.6 Test Costs Tab
- [ ] Click **"💰 Costs"** tab
- [ ] If costs exist:
  - [ ] Verify 4 colored cards displayed:
    - **Material Cost** (blue card)
    - **Labor Cost** (green card)
    - **Overhead Cost** (yellow card)
    - **Total Cost** (purple card)
  - [ ] Verify all amounts formatted as EUR currency
  - [ ] Verify "📊 Cost Breakdown" placeholder section
- [ ] If no costs:
  - [ ] Verify empty state: "💰 No cost information available"

#### 5.7 Test Audit Tab
- [ ] Click **"🔍 Audit"** tab
- [ ] Verify audit information displayed:
  - Created At (with time)
  - Created By (username or "-")
  - Updated At (with time)
  - Updated By (username or "-")
- [ ] Verify dates formatted with time (MMM DD, YYYY HH:MM AM/PM)
- [ ] Verify "📝 Change History" placeholder section

#### 5.8 Test Modal Controls
- [ ] Test tab switching (click each tab multiple times)
- [ ] Verify active tab has blue underline
- [ ] Click **"✕"** button in top-right → Verify modal closes
- [ ] Click **"Close"** button in footer → Verify modal closes
- [ ] Click outside modal (on dark overlay) → Should NOT close (intentional)

#### 5.9 Test Loading State
- [ ] (Difficult to test manually, but should show):
  - Spinner animation (⏳)
  - "Loading order details..." message
  - White background modal

---

## 🐛 Known Issues / Expected Behavior

1. **Native Confirm Dialog**: Currently using browser's `confirm()` for delete confirmation. Consider custom modal in future.

2. **Empty States**: If backend returns no lines/routing/costs, empty states are shown. This is expected for newly created orders.

3. **API Errors**: If API returns 401, toast error shown and modal auto-closes.

4. **Form Validation**: Real-time validation only triggers on blur or submit. This is standard react-hook-form behavior.

5. **UOM Deletion**: Backend should prevent deletion of UOMs used by items. Test this by trying to delete "PCS" (used by many items).

---

## 📊 Test Results Template

```
TEST SESSION: [Date/Time]
TESTER: [Name]
ENVIRONMENT: Docker Compose (local)

| Test | Status | Notes |
|------|--------|-------|
| Items - View List | ✅ / ❌ | |
| Items - Create | ✅ / ❌ | |
| Items - Edit | ✅ / ❌ | |
| Items - Delete | ✅ / ❌ | |
| Items - Search | ✅ / ❌ | |
| UOMs - View List | ✅ / ❌ | |
| UOMs - Create | ✅ / ❌ | |
| UOMs - Edit | ✅ / ❌ | |
| UOMs - Delete | ✅ / ❌ | |
| Locations - View List | ✅ / ❌ | |
| Locations - Create | ✅ / ❌ | |
| Locations - Edit | ✅ / ❌ | |
| Suppliers - View List | ✅ / ❌ | |
| Suppliers - Create | ✅ / ❌ | |
| Suppliers - Edit | ✅ / ❌ | |
| Order Details - General | ✅ / ❌ | |
| Order Details - Lines | ✅ / ❌ | |
| Order Details - Routing | ✅ / ❌ | |
| Order Details - Costs | ✅ / ❌ | |
| Order Details - Audit | ✅ / ❌ | |

OVERALL STATUS: ✅ PASS / ❌ FAIL
```

---

## 🚀 Quick Test Commands

```bash
# Check if containers are running
docker-compose ps

# View backend logs (for API errors)
docker-compose logs -f backend

# View frontend logs (for React errors)
docker-compose logs -f frontend

# Restart frontend (if needed)
docker-compose restart frontend

# Check API health
curl http://localhost:5000/api/health

# Get JWT token (for manual API testing)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

---

## 📝 Notes for Next Steps

After completing these tests:

1. **Error Boundaries**: Wrap forms in error boundaries (next todo item)
2. **Export Functionality**: Add PDF/Excel export for BOMs and Routings
3. **Bulk Operations**: Add checkbox selection for bulk release/cancel
4. **Custom Confirm Modal**: Replace native `confirm()` with custom component
5. **Change History**: Implement actual change tracking in Audit tab
6. **Cost Breakdown Chart**: Add visual chart for cost breakdown

---

## 🎯 Success Criteria

✅ All forms open without errors  
✅ All validation rules work correctly  
✅ All CRUD operations complete successfully  
✅ Toast notifications appear for all actions  
✅ Modal closes after successful operations  
✅ Search functionality filters correctly  
✅ Production Order Details modal displays all tabs  
✅ No TypeScript errors in browser console  
✅ No 500 errors from backend API  

---

**End of Test Guide**
