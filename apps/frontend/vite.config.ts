import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, Vite serves the UI on :5173 and transparently proxies any
// request starting with /api to the FastAPI server on :8000.
// This means frontend code can just call "/api/v1/health" — the same
// relative URL that works in production behind Nginx. No env juggling.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
