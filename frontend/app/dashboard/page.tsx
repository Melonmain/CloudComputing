"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, RefreshCw, CheckCircle2, Circle, LayoutList } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { api, type Todo } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { TodoList } from "@/components/todos/TodoList";
import { CreateTodoDialog } from "@/components/todos/CreateTodoDialog";
import { EditTodoDialog } from "@/components/todos/EditTodoDialog";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

type Filter = "all" | "open" | "done";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [editTarget, setEditTarget] = useState<Todo | null>(null);
  const [editOpen, setEditOpen] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  async function fetchTodos() {
    setError(null);
    setLoading(true);
    try {
      setTodos(await api.todos.list());
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Fehler beim Laden";
      setError(msg);
      toast.error("Aufgaben konnten nicht geladen werden", { description: msg });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { if (user) fetchTodos(); }, [user]);

  const openCount = todos.filter((t) => !t.completed).length;
  const doneCount = todos.filter((t) => t.completed).length;

  if (authLoading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 className="w-10 h-10 animate-spin text-primary" />
    </div>
  );
  if (!user) return null;

  const filters: { key: Filter; label: string; count: number; icon: React.ReactNode }[] = [
    { key: "all",  label: "Alle Aufgaben", count: todos.length, icon: <LayoutList className="w-5 h-5" /> },
    { key: "open", label: "Offen",         count: openCount,    icon: <Circle className="w-5 h-5" /> },
    { key: "done", label: "Erledigt",      count: doneCount,    icon: <CheckCircle2 className="w-5 h-5" /> },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <div className="flex flex-1 w-full">

        {/* ── Sidebar ─────────────────────────────────────────────────────── */}
        <aside className="hidden lg:flex flex-col w-72 xl:w-80 shrink-0 border-r border-border/60 bg-card px-6 py-8 gap-8 sticky top-20 h-[calc(100vh-5rem)] overflow-y-auto">

          {/* Stats */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground px-1">Übersicht</p>
            <div className="space-y-2">
              {[
                { label: "Gesamt",   value: todos.length, color: "text-foreground",                     bg: "bg-muted/60" },
                { label: "Offen",    value: openCount,    color: "text-primary",                         bg: "bg-primary/10" },
                { label: "Erledigt", value: doneCount,    color: "text-green-600 dark:text-green-400",  bg: "bg-green-500/10" },
              ].map((s) => (
                <div key={s.label} className={`flex items-center justify-between rounded-xl px-4 py-3 ${s.bg}`}>
                  <span className="text-base font-medium text-foreground">{s.label}</span>
                  <span className={`text-2xl font-bold ${s.color}`}>{s.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Filter nav */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground px-1">Filter</p>
            <nav className="space-y-1">
              {filters.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-xl text-base font-medium transition-all ${
                    filter === f.key
                      ? "gradient-brand text-white shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  }`}
                >
                  <span className="flex items-center gap-3">
                    {f.icon}
                    {f.label}
                  </span>
                  <span className={`text-sm font-bold px-2 py-0.5 rounded-full ${
                    filter === f.key ? "bg-white/20" : "bg-muted text-muted-foreground"
                  }`}>
                    {f.count}
                  </span>
                </button>
              ))}
            </nav>
          </div>
        </aside>

        {/* ── Main content ─────────────────────────────────────────────────── */}
        <main className="flex-1 min-w-0 px-6 xl:px-10 py-8 space-y-6">

          {/* Topbar */}
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-foreground">
                {filters.find(f => f.key === filter)?.label ?? "Aufgaben"}
              </h1>
              <p className="text-muted-foreground text-base mt-1">
                Hallo, <span className="font-semibold text-foreground">{user.username}</span> —{" "}
                {openCount === 0 ? "alles erledigt!" : `${openCount} Aufgabe${openCount !== 1 ? "n" : ""} offen`}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="icon" onClick={fetchTodos} disabled={loading} title="Aktualisieren" className="h-11 w-11">
                <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
              </Button>
              <CreateTodoDialog onCreated={(t) => setTodos((p) => [t, ...p])} />
            </div>
          </div>

          {/* Mobile filter pills (only visible below lg) */}
          <div className="flex gap-2 flex-wrap lg:hidden">
            {filters.map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  filter === f.key
                    ? "gradient-brand text-white shadow-sm"
                    : "bg-muted text-muted-foreground hover:bg-accent"
                }`}
              >
                {f.label}
                <span className={`text-xs px-1.5 rounded-full ${filter === f.key ? "bg-white/20" : "bg-background"}`}>
                  {f.count}
                </span>
              </button>
            ))}
          </div>

          {/* Content */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-32 gap-4">
              <Loader2 className="w-10 h-10 animate-spin text-primary" />
              <p className="text-base text-muted-foreground">Aufgaben werden geladen…</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-32 gap-4 text-center">
              <p className="text-destructive font-medium text-lg">{error}</p>
              <Button variant="outline" size="lg" onClick={fetchTodos}>Erneut versuchen</Button>
            </div>
          ) : (
            <TodoList
              todos={todos}
              filter={filter}
              onUpdated={(u) => setTodos((p) => p.map((t) => t.id === u.id ? u : t))}
              onDeleted={(id) => setTodos((p) => p.filter((t) => t.id !== id))}
              onEditRequest={(t) => { setEditTarget(t); setEditOpen(true); }}
            />
          )}
        </main>
      </div>

      <EditTodoDialog todo={editTarget} open={editOpen} onOpenChange={setEditOpen}
        onUpdated={(u) => setTodos((p) => p.map((t) => t.id === u.id ? u : t))} />
    </div>
  );
}
