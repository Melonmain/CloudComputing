"use client";

import { ClipboardList } from "lucide-react";
import { TodoCard } from "@/components/todos/TodoCard";
import { type Todo } from "@/lib/api";

interface Props {
  todos: Todo[];
  filter: "all" | "open" | "done";
  onUpdated: (todo: Todo) => void;
  onDeleted: (id: string) => void;
  onEditRequest: (todo: Todo) => void;
}

export function TodoList({ todos, filter, onUpdated, onDeleted, onEditRequest }: Props) {
  const filtered = todos.filter((t) => {
    if (filter === "open") return !t.completed;
    if (filter === "done") return t.completed;
    return true;
  });

  if (filtered.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-28 gap-5 text-center">
        <div className="p-6 rounded-full bg-primary/10">
          <ClipboardList className="w-14 h-14 text-primary/60" />
        </div>
        <div>
          <p className="font-semibold text-xl text-foreground">
            {filter === "done"
              ? "Noch nichts erledigt"
              : filter === "open"
              ? "Alle Aufgaben erledigt!"
              : "Keine Aufgaben vorhanden"}
          </p>
          <p className="text-base text-muted-foreground mt-2">
            {filter === "all" ? "Erstelle deine erste Aufgabe mit dem Button oben." : ""}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {filtered.map((todo) => (
        <TodoCard
          key={todo.id}
          todo={todo}
          onUpdated={onUpdated}
          onDeleted={onDeleted}
          onEditRequest={onEditRequest}
        />
      ))}
    </div>
  );
}
