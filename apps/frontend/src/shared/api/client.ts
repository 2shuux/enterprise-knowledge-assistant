/**
 * Single axios instance for the whole app.
 *
 * Request interceptor: attaches the access token to every call.
 * Response interceptor: on 401, silently exchanges the refresh token for a
 * new pair and retries the original request ONCE. All concurrent 401s share
 * one refresh call (single-flight) — otherwise five parallel requests would
 * trigger five refreshes and rotation would kill four of them.
 */
import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "../../features/auth/store";

export const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshInFlight: Promise<string> | null = null;

async function refreshTokens(): Promise<string> {
  const { refreshToken, setTokens, clear } = useAuthStore.getState();
  if (!refreshToken) throw new Error("No refresh token");
  try {
    // Plain axios (not `api`) — the interceptor must not intercept itself.
    const { data } = await axios.post("/api/v1/auth/refresh", {
      refresh_token: refreshToken,
    });
    setTokens({ accessToken: data.access_token, refreshToken: data.refresh_token });
    return data.access_token as string;
  } catch (err) {
    clear(); // refresh failed → session is dead → back to login
    throw err;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const isAuthCall = original?.url?.startsWith("/auth/");
    if (error.response?.status === 401 && !original._retry && !isAuthCall) {
      original._retry = true;
      refreshInFlight = refreshInFlight ?? refreshTokens();
      try {
        const newToken = await refreshInFlight;
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } finally {
        refreshInFlight = null;
      }
    }
    return Promise.reject(error);
  }
);
