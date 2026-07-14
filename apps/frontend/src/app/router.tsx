import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppLayout } from "../shared/components/AppLayout";
import { ComingSoon } from "../pages/ComingSoon";
import { Landing } from "../pages/Landing";

/**
 * Route table. Placeholder pages carry the milestone in which they'll be
 * built — the roadmap is visible inside the running app itself.
 * Auth guards (RequireAuth / RequireAdmin) wrap these routes in Milestone 1.
 */
export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<AppLayout />}>
          <Route path="/chat" element={<ComingSoon feature="AI Chat" milestone="M3–M4" />} />
          <Route path="/documents" element={<ComingSoon feature="Document Library" milestone="M2" />} />
          <Route path="/search" element={<ComingSoon feature="Hybrid Search" milestone="M5" />} />
          <Route path="/admin" element={<ComingSoon feature="Admin Dashboard" milestone="M6" />} />
        </Route>
        <Route path="*" element={<ComingSoon feature="This page" milestone="never — it's a 404" />} />
      </Routes>
    </BrowserRouter>
  );
}
