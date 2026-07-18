/**
 * Route guards — declarative authorization at the routing layer.
 * <RequireAuth> bounces anonymous visitors to /login (remembering where they
 * were headed); <RequireAdmin> additionally blocks non-admins.
 */
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "../features/auth/store";

export function RequireAuth() {
  const user = useAuthStore((s) => s.user);
  const location = useLocation();
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <Outlet />;
}

export function RequireAdmin() {
  const user = useAuthStore((s) => s.user);
  if (user?.role !== "ADMIN") return <Navigate to="/chat" replace />;
  return <Outlet />;
}
