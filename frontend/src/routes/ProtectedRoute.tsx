
import { Navigate, Outlet, useLocation } from 'react-router-dom';
export default function ProtectedRoute() {
  const location = useLocation();
  const access = localStorage.getItem('access_token');
  if (!access) return <Navigate to="/login" replace state={{ from: location }} />;
  return <Outlet />;
}
