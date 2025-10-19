import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '@/routes/ProtectedRoute';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import NotFound from '@/pages/NotFound';
import DashboardLayout from '@/layouts/DashboardLayout';
import '@/i18n';
import MasterData from '@/pages/MasterData';
import Production from '@/pages/Production';
import ProductionAdmin from '@/pages/ProductionAdmin';
import ProductionDesign from '@/pages/ProductionDesign';
import ProductionCapabilities from '@/pages/ProductionCapabilities';
import ProductionPlanning from '@/pages/ProductionPlanning';
import ProductionExecution from '@/pages/ProductionExecution';
import ProductionCosting from '@/pages/ProductionCosting';
import ProductionTasks from '@/pages/ProductionTasks';
import WorkCenters from '@/pages/WorkCenters';
import MachineCenters from '@/pages/MachineCenters';
import SalesOrders from '@/pages/SalesOrders';
import SalesInvoices from '@/pages/SalesInvoices';
import Sales from '@/pages/Sales';
import CRM from '@/pages/CRM';
import ModuleInDevelopment from '@/pages/ModuleInDevelopment';
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/masterdata" element={<MasterData />} />
            <Route path="/production" element={<Production />} />
            <Route path="/production/admin" element={<ProductionAdmin />} />
            <Route path="/production/design" element={<ProductionDesign />} />
            <Route path="/production/capabilities" element={<ProductionCapabilities />} />
            <Route path="/production/planning" element={<ProductionPlanning />} />
            <Route path="/production/execution" element={<ProductionExecution />} />
            <Route path="/production/costing" element={<ProductionCosting />} />
            <Route path="/production/tasks" element={<ProductionTasks />} />
            <Route path="/production/workcenters" element={<WorkCenters />} />
            <Route path="/production/machines" element={<MachineCenters />} />
            <Route path="/crm" element={<CRM />} />
            <Route path="/sales" element={<Sales />} />
            <Route path="/sales/orders" element={<SalesOrders />} />
            <Route path="/sales/invoices" element={<SalesInvoices />} />
            {/* Module routes */}
            <Route path="/module/:moduleId" element={<ModuleInDevelopment />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
