/**
 * Global auth state (Zustand + persist).
 *
 * Persisted to localStorage so a page refresh doesn't log you out.
 * Note for later hardening (M7): localStorage is readable by any JS on the
 * page, so an XSS bug could steal tokens. The stricter pattern is an
 * httpOnly cookie for the refresh token — we document the trade-off in
 * the README and keep the simpler model while learning.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: "ADMIN" | "USER";
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  setSession: (s: { user: AuthUser; accessToken: string; refreshToken: string }) => void;
  setTokens: (s: { accessToken: string; refreshToken: string }) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      setSession: ({ user, accessToken, refreshToken }) =>
        set({ user, accessToken, refreshToken }),
      setTokens: ({ accessToken, refreshToken }) => set({ accessToken, refreshToken }),
      clear: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    { name: "eka-auth" }
  )
);
