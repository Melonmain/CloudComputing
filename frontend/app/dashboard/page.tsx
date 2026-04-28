"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, RefreshCw } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { api, type Todo } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { TodoList } from "@/components/todos/TodoList";
import { CreateTodoDialog } from "@/components/todos/CreateTodoDialog";
import { EditTodoDialog } from "@/components/todos/EditTodoDialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  async function fetchTodos() {
    setError(null);
    setLoading(true);
    try {
      const data = await api.todos.list();
      setTodos(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Fehler beim Laden";
      setError(msg);
      toast.error("Aufgaben konnten nicht geladen werden", { description: msg });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user) fetchTodos();
  }, [user]);

  const openCount = todos.filter((t) => !t.completed).length;
  const doneCount = todos.filter((t) => t.completed).length;

  function handleCreated(todo: Todo) {
    setTodos((prev) => [todo, ...prev]);
  }

  function handleUpdated(updated: Todo) {
    setTodos((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  }

  function handleDeleted(id: string) {
    setTodos((prev) => prev.filter((t) => t.id !== id));
  }

  function handleEditRequest(todo: Todo) {
    setEditTarget(todo);
    setEditOpen(true);
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <>
      <Header />

      <main className="max-w-6xl mx-auto px-6 lg:px-10 py-10 space-y-8">
        {/* Stats bar */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Gesamt", value: todos.length, color: "text-foreground" },
            { label: "Offen", value: openCount, color: "text-primary" },
            { label: "Erledigt", value: doneCount, color: "text-green-600 dark:text-green-400" },
          ].map((s) => (
            <div
              key={s.label}
              className="bg-card border border-border/60 rounded-2xl px-6 py-5 flex flex-col gap-1 shadow-sm"
            >
              <span className={`text-3xl font-bold ${s.color}`}>{s.value}</span>
              <span className="text-sm text-muted-foreground font-medium">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Page title & action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Meine Aufgaben</h1>
            <p className="text-muted-foreground text-base mt-1">
              {todos.length === 0
                ? "Noch keine Aufgaben vorhanden"
                : `${openCount} offen · ${doneCount} erledigt`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="icon"
              onClick={fetchTodos}
              disabled={loading}
              title="Aktualisieren"
              className="h-11 w-11"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
            </Button>
            <CreateTodoDialog onCreated={handleCreated} />
          </div>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-3 flex-wrap">
          {(["all", "open", "done"] as Filter[]).map((f) => {
            const labels: Record<Filter, string> = { all: "Alle", open: "Offen", done: "Erledigt" };
            const counts: Record<Filter, number> = { all: todos.length, open: openCount, done: doneCount };
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`flex items-center gap-2 px-5 py-2 rounded-full text-base font-medium transition-all ${
                  filter === f
                    ? "gradient-brand text-white shadow-sm"
                    : "bg-muted text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                }`}
              >
                {labels[f]}
                <Badge
                  variant="secondary"
                  className={`text-xs px-2 py-0 ${filter === f ? "bg-white/20 text-white" : ""}`}
                >
                  {counts[f]}
                </Badge>
              </button>
            );
          })}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-28 gap-4">
            <Loader2 className="w-10 h-10 animate-spin text-primary" />
            <p className="text-base text-muted-foreground">Aufgaben werden geladen…</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-28 gap-5 text-center">
            <p className="text-destructive font-medium text-lg">{error}</p>
            <Button variant="outline" size="lg" onClick={fetchTodos}>
              Erneut versuchen
            </Button>
          </div>
        ) : (
          <TodoList
            todos={todos}
            filter={filter}
            onUpdated={handleUpdated}
            onDeleted={handleDeleted}
            onEditRequest={handleEditRequest}
          />
        )}
      </main>

      <EditTodoDialog
        todo={editTarget}
        open={editOpen}
        onOpenChange={setEditOpen}
        onUpdated={handleUpdated}
      />
    </>
  );
}
