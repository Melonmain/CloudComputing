"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface User {
  username: string;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const USER_STORAGE_KEY = "todo_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Restore session from localStorage (mock — replace with JWT validation)
    const stored = localStorage.getItem(USER_STORAGE_KEY);
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem(USER_STORAGE_KEY);
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const res = await api.auth.login({ username, password });
    const u: User = { username: res.username };
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(u));
    setUser(u);
    router.push("/dashboard");
  }, [router]);

  const register = useCallback(async (username: string, password: string) => {
    const res = await api.auth.register({ username, password });
    const u: User = { username: res.username };
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(u));
    setUser(u);
    router.push("/dashboard");
  }, [router]);

  const logout = useCallback(async () => {
    await api.auth.logout().catch(() => {});
    localStorage.removeItem(USER_STORAGE_KEY);
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
