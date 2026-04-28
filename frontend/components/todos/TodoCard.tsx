"use client";

import { useState } from "react";
import { MoreHorizontal, Pencil, Trash2, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { api, type Todo } from "@/lib/api";
import { toast } from "sonner";

interface Props {
  todo: Todo;
  onUpdated: (todo: Todo) => void;
  onDeleted: (id: string) => void;
  onEditRequest: (todo: Todo) => void;
}

export function TodoCard({ todo, onUpdated, onDeleted, onEditRequest }: Props) {
  const [toggling, setToggling] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleToggle() {
    setToggling(true);
    try {
      const updated = await api.todos.toggle(todo);
      onUpdated(updated);
      toast.success(updated.completed ? "Als erledigt markiert" : "Als offen markiert", {
        description: updated.title,
      });
    } catch (err) {
      toast.error("Fehler", { description: err instanceof Error ? err.message : "" });
    } finally {
      setToggling(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await api.todos.delete(todo.id);
      onDeleted(todo.id);
      toast.success("Aufgabe gelöscht", { description: todo.title });
    } catch (err) {
      toast.error("Fehler beim Löschen", {
        description: err instanceof Error ? err.message : "",
      });
      setDeleting(false);
    }
  }

  const createdAt = new Date(todo.created_at).toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  return (
    <Card
      className={`card-hover border-border/60 ${todo.completed ? "opacity-60" : ""} ${
        deleting ? "pointer-events-none opacity-40" : ""
      }`}
    >
      <CardContent className="p-6 flex items-start gap-5">
        {/* Checkbox */}
        <div className="pt-1 flex-shrink-0">
          {toggling ? (
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
          ) : (
            <Checkbox
              checked={todo.completed}
              onCheckedChange={handleToggle}
              className="w-5 h-5 data-[state=checked]:bg-primary data-[state=checked]:border-primary"
            />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <p
              className={`font-semibold text-lg leading-snug ${
                todo.completed ? "line-through text-muted-foreground" : "text-foreground"
              }`}
            >
              {todo.title}
            </p>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-foreground flex-shrink-0"
                >
                  <MoreHorizontal className="w-5 h-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44">
                <DropdownMenuItem className="text-base py-2" onClick={() => onEditRequest(todo)}>
                  <Pencil className="w-4 h-4 mr-2" />
                  Bearbeiten
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive text-base py-2"
                  onClick={handleDelete}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Löschen
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {todo.description && (
            <p className="text-base text-muted-foreground mt-2 line-clamp-2 leading-relaxed">
              {todo.description}
            </p>
          )}

          <div className="flex items-center gap-3 mt-4">
            <Badge
              variant={todo.completed ? "secondary" : "outline"}
              className={`text-base px-3 py-0.5 ${
                todo.completed
                  ? "bg-primary/10 text-primary border-primary/20"
                  : "text-muted-foreground"
              }`}
            >
              {todo.completed ? "Erledigt" : "Offen"}
            </Badge>
            <span className="text-base text-muted-foreground">{createdAt}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
