import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '@/routes/ProtectedRoute';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import NotFound from '@/pages/NotFound';
import DashboardLayout from '@/layouts/DashboardLayout';
import '@/i18n';
import MasterData from '@/pages/MasterData';
import ProductionAdmin from '@/pages/ProductionAdmin';
import WorkCenters from '@/pages/WorkCenters';
import MachineCenters from '@/pages/MachineCenters';
import SalesOrders from '@/pages/SalesOrders';
import SalesInvoices from '@/pages/SalesInvoices';
import CRM from '@/pages/CRM';
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/masterdata" element={<MasterData />} />
            <Route path="/production/admin" element={<ProductionAdmin />} />
            <Route path="/production/workcenters" element={<WorkCenters />} />
            <Route path="/production/machines" element={<MachineCenters />} />
            <Route path="/crm" element={<CRM />} />
            <Route path="/sales/orders" element={<SalesOrders />} />
            <Route path="/sales/invoices" element={<SalesInvoices />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
