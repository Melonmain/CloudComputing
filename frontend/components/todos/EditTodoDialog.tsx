"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api, type Todo } from "@/lib/api";
import { toast } from "sonner";

interface Props {
  todo: Todo | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdated: (todo: Todo) => void;
}

export function EditTodoDialog({ todo, open, onOpenChange, onUpdated }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (todo) {
      setTitle(todo.title);
      setDescription(todo.description ?? "");
    }
  }, [todo]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!todo) return;
    setLoading(true);
    try {
      const updated = await api.todos.update(todo.id, {
        title,
        description: description || null,
      });
      onUpdated(updated);
      toast.success("Aufgabe aktualisiert");
      onOpenChange(false);
    } catch (err) {
      toast.error("Fehler beim Aktualisieren", {
        description: err instanceof Error ? err.message : "Unbekannter Fehler",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Aufgabe bearbeiten</DialogTitle>
          <DialogDescription>Ändere Titel oder Beschreibung der Aufgabe.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <div className="space-y-2">
            <label className="text-base font-medium" htmlFor="edit-title">
              Titel
            </label>
            <Input
              id="edit-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              autoFocus
              className="h-12 text-base"
            />
          </div>
          <div className="space-y-2">
            <label className="text-base font-medium" htmlFor="edit-desc">
              Beschreibung
            </label>
            <Textarea
              id="edit-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="resize-none"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" size="lg" onClick={() => onOpenChange(false)}>
              Abbrechen
            </Button>
            <Button
              type="submit"
              size="lg"
              className="gradient-brand text-white border-0 hover:opacity-90"
              disabled={loading || !title.trim()}
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Speichern"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
