import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({ adminOnly = false }) {
  const { loading, isAuthenticated, isAdmin } = useAuth();
  if (loading) return <div className="screen-loader"><div className="loader-orb" /><span>Preparing your farming assistant…</span></div>;
  if (!isAuthenticated) return <Navigate to="/auth" replace />;
  if (adminOnly && !isAdmin) return <Navigate to="/chat" replace />;
  return <Outlet />;
}
