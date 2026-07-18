import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Chat } from "../pages/Chat";
import { ComingSoon } from "../pages/ComingSoon";
import { Documents } from "../pages/Documents";
import { Landing } from "../pages/Landing";
import { Login } from "../pages/Login";
import { Register } from "../pages/Register";
import { AppLayout } from "../shared/components/AppLayout";
import { RequireAdmin, RequireAuth } from "./guards";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* public */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* authenticated */}
        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            <Route path="/chat" element={<Chat />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/search" element={<ComingSoon feature="Hybrid Search" milestone="M5" />} />

            {/* admin-only */}
            <Route element={<RequireAdmin />}>
              <Route path="/admin" element={<ComingSoon feature="Admin Dashboard" milestone="M6" />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<ComingSoon feature="This page" milestone="never — it's a 404" />} />
      </Routes>
    </BrowserRouter>
  );
}
