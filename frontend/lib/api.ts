const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(body || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Todos ─────────────────────────────────────────────────────────────────────

export const api = {
  todos: {
    list: (): Promise<Todo[]> => request("/todos/"),

    create: (data: TodoCreate): Promise<Todo> =>
      request("/todos/", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (id: string, data: TodoUpdate): Promise<Todo> =>
      request(`/todos/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),

    delete: (id: string): Promise<void> =>
      request(`/todos/${id}`, { method: "DELETE" }),

    toggle: (todo: Todo): Promise<Todo> =>
      request(`/todos/${todo.id}`, {
        method: "PUT",
        body: JSON.stringify({ completed: !todo.completed }),
      }),
  },

  // ── Auth (mock, forwards to FastAPI which will call the real login server) ──
  auth: {
    login: (data: AuthRequest) =>
      request<{ message: string; username: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    register: (data: AuthRequest) =>
      request<{ message: string; username: string }>("/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    logout: () => request<{ message: string }>("/auth/logout", { method: "POST" }),
  },

  health: () => request<{ status: string; version: string; mode: string }>("/health"),
};
