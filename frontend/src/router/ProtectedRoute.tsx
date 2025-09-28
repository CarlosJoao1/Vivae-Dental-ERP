import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function ProtectedRoute() {
  const { loading, accessToken } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center">
        <div className="text-gray-600">A carregar sessão…</div>
      </div>
    );
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
