
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '@/routes/ProtectedRoute';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import NotFound from '@/pages/NotFound';
import DashboardLayout from '@/layouts/DashboardLayout';
import '@/i18n';
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Dashboard />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
