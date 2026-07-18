import { api } from "../../shared/api/client";
import { useAuthStore, type AuthUser } from "./store";

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const { data } = await api.post<LoginResponse>("/auth/login", { email, password });
  useAuthStore.getState().setSession({
    user: data.user,
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
  });
  return data.user;
}

export async function register(email: string, password: string, fullName: string) {
  await api.post("/auth/register", { email, password, full_name: fullName });
  return login(email, password); // auto-login after signup
}

export async function logout(): Promise<void> {
  const { refreshToken, clear } = useAuthStore.getState();
  try {
    if (refreshToken) await api.post("/auth/logout", { refresh_token: refreshToken });
  } finally {
    clear(); // clear locally even if the server call fails
  }
}
