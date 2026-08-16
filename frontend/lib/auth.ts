import { apiRequest } from "./api";
import type {
  AuthResponse,
  LoginRequest,
  MeResponse,
  Organization,
  RegisterRequest,
  TokenPairResponse,
  User,
} from "../types/auth";

export const ACCESS_TOKEN_KEY = "nexus_access_token";
export const REFRESH_TOKEN_KEY = "nexus_refresh_token";
export const USER_KEY = "nexus_user";
export const ORG_KEY = "nexus_organization";

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function getStoredOrganization(): Organization | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(ORG_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Organization;
  } catch {
    return null;
  }
}

export function setAuthSession(auth: AuthResponse): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, auth.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, auth.refresh_token);
  localStorage.setItem(USER_KEY, JSON.stringify(auth.user));
  localStorage.setItem(ORG_KEY, JSON.stringify(auth.organization));
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(ORG_KEY);
}

export function isAuthenticated(): boolean {
  return !!getStoredAccessToken();
}

export async function login(
  credentials: LoginRequest,
): Promise<AuthResponse> {
  const data = await apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
  setAuthSession(data);
  return data;
}

export async function register(
  data: RegisterRequest,
): Promise<AuthResponse> {
  const res = await apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
  setAuthSession(res);
  return res;
}

export async function refreshToken(
  refresh_token: string,
): Promise<TokenPairResponse> {
  const res = await apiRequest<TokenPairResponse>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token }),
  });
  if (typeof window !== "undefined") {
    localStorage.setItem(ACCESS_TOKEN_KEY, res.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, res.refresh_token);
  }
  return res;
}

export async function getMe(
  accessToken?: string,
): Promise<MeResponse> {
  return apiRequest<MeResponse>(
    "/auth/me",
    {
      method: "GET",
    },
    accessToken,
  );
}

export function logout(): void {
  clearAuthSession();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}