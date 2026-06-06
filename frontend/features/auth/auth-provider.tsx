"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";
import { useRouter } from "next/navigation";

import { apiFetch, loginRequest } from "@/lib/api";
import type { TokenResponse, User, UserRole } from "@/lib/types";

const ACCESS_TOKEN_KEY = "ata_pims_access_token";
const REFRESH_TOKEN_KEY = "ata_pims_refresh_token";

type AuthContextValue = {
  user: User | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
  hasRole: (...roles: UserRole[]) => boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredToken(key: string) {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

function storeTokens(tokens: TokenResponse) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

function clearTokens() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async (token: string) => {
    const currentUser = await apiFetch<User>("/auth/me", { token });
    setUser(currentUser);
  }, []);

  const refreshAccessToken = useCallback(async () => {
    const refreshToken = readStoredToken(REFRESH_TOKEN_KEY);
    if (!refreshToken) return null;
    const tokens = await apiFetch<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    storeTokens(tokens);
    setAccessToken(tokens.access_token);
    return tokens.access_token;
  }, []);

  const refreshMe = useCallback(async () => {
    const token = accessToken ?? readStoredToken(ACCESS_TOKEN_KEY);
    if (!token) {
      setUser(null);
      return;
    }
    try {
      await loadMe(token);
      setAccessToken(token);
    } catch {
      const newToken = await refreshAccessToken();
      if (newToken) {
        await loadMe(newToken);
      } else {
        clearTokens();
        setAccessToken(null);
        setUser(null);
      }
    }
  }, [accessToken, loadMe, refreshAccessToken]);

  useEffect(() => {
    refreshMe().finally(() => setLoading(false));
  }, [refreshMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await loginRequest(email, password);
      storeTokens(tokens);
      setAccessToken(tokens.access_token);
      await loadMe(tokens.access_token);
      router.push("/dashboard");
    },
    [loadMe, router]
  );

  const logout = useCallback(async () => {
    const refreshToken = readStoredToken(REFRESH_TOKEN_KEY);
    if (refreshToken) {
      await apiFetch("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken })
      }).catch(() => undefined);
    }
    clearTokens();
    setAccessToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  const hasRole = useCallback(
    (...roles: UserRole[]) => {
      return !!user && roles.includes(user.role);
    },
    [user]
  );

  const value = useMemo(
    () => ({ user, accessToken, loading, login, logout, refreshMe, hasRole }),
    [accessToken, hasRole, loading, login, logout, refreshMe, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
