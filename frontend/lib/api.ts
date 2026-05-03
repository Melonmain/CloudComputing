import { TOKEN_STORAGE_KEY } from "@/lib/auth";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const LOGIN_URL = process.env.NEXT_PUBLIC_LOGIN_URL ?? "http://localhost:8001";

export interface Todo {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface TodoCreate {
  title: string;
  description?: string | null;
  completed?: boolean;
}

export interface TodoUpdate {
  title?: string;
  description?: string | null;
  completed?: boolean;
}

export interface AuthRequest {
  username: string;
  password: string;
}

function getAuthHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const { headers: initHeaders, ...restInit } = init ?? {};
  const res = await fetch(`${baseUrl}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...initHeaders },
    ...restInit,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    let message = `HTTP ${res.status}`;
    try {
      const json = JSON.parse(body);
      message = json.detail ?? json.message ?? body;
    } catch {
      message = body || message;
    }
    throw new Error(message);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function backendRequest<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(BACKEND_URL, path, {
    ...init,
    headers: { ...getAuthHeader(), ...init?.headers },
  });
}

// ── Todos ─────────────────────────────────────────────────────────────────────

export const api = {
  todos: {
    list: (): Promise<Todo[]> => backendRequest("/todos/"),

    create: (data: TodoCreate): Promise<Todo> =>
      backendRequest("/todos/", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (id: string, data: TodoUpdate): Promise<Todo> =>
      backendRequest(`/todos/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),

    delete: (id: string): Promise<void> =>
      backendRequest(`/todos/${id}`, { method: "DELETE" }),

    toggle: (todo: Todo): Promise<Todo> =>
      backendRequest(`/todos/${todo.id}`, {
        method: "PUT",
        body: JSON.stringify({ completed: !todo.completed }),
      }),
  },

  // ── Auth (standalone login service) ──
  auth: {
    login: (data: AuthRequest) =>
      request<{ message: string; username: string; access_token: string; token_type: string }>(LOGIN_URL, "/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    register: (data: AuthRequest) =>
      request<{ message: string; username: string; access_token: string; token_type: string }>(LOGIN_URL, "/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    logout: () => request<{ message: string }>(LOGIN_URL, "/auth/logout", { method: "POST" }),
  },

  health: () => request<{ status: string; version: string; mode: string }>(BACKEND_URL, "/health"),
};
