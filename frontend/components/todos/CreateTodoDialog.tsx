"use client";

import { useState, type FormEvent } from "react";
import { PlusCircle, Loader2 } from "lucide-react";
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
  DialogTrigger,
} from "@/components/ui/dialog";
import { api, type Todo } from "@/lib/api";
import { toast } from "sonner";

interface Props {
  onCreated: (todo: Todo) => void;
}

export function CreateTodoDialog({ onCreated }: Props) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const todo = await api.todos.create({ title, description: description || null });
      onCreated(todo);
      toast.success("Aufgabe erstellt", { description: title });
      setOpen(false);
      setTitle("");
      setDescription("");
    } catch (err) {
      toast.error("Fehler beim Erstellen", {
        description: err instanceof Error ? err.message : "Unbekannter Fehler",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="h-11 px-5 text-base gradient-brand text-white border-0 hover:opacity-90 transition-opacity gap-2">
          <PlusCircle className="w-5 h-5" />
          Neue Aufgabe
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Neue Aufgabe erstellen</DialogTitle>
          <DialogDescription>Füge eine neue Aufgabe zu deiner Liste hinzu.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <div className="space-y-2">
            <label className="text-base font-medium" htmlFor="create-title">
              Titel <span className="text-destructive">*</span>
            </label>
            <Input
              id="create-title"
              placeholder="Was möchtest du erledigen?"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              autoFocus
              className="h-12 text-base"
            />
          </div>
          <div className="space-y-2">
            <label className="text-base font-medium" htmlFor="create-desc">
              Beschreibung <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <Textarea
              id="create-desc"
              placeholder="Weitere Details…"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="resize-none"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" size="lg" onClick={() => setOpen(false)}>
              Abbrechen
            </Button>
            <Button
              type="submit"
              size="lg"
              className="gradient-brand text-white border-0 hover:opacity-90"
              disabled={loading || !title.trim()}
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Erstellen"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
