"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Cloud, Loader2, AlertCircle } from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function RegisterPage() {
  const { register } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Die Passwörter stimmen nicht überein.");
      return;
    }
    setLoading(true);
    try {
      await register(username, password);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "";
      setError(msg.includes("already exists")
        ? "Benutzername bereits vergeben."
        : msg || "Registrierung fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center gradient-subtle p-6 relative">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="w-full max-w-xl space-y-10">

        {/* Brand */}
        <div className="flex flex-col items-center gap-4">
          <div className="gradient-brand p-4 rounded-2xl shadow-xl">
            <Cloud className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-5xl font-bold tracking-tight text-foreground">Cloud Todo</h1>
          <p className="text-lg text-muted-foreground">Starte organisiert durch den Tag.</p>
        </div>

        <div className="bg-card border border-border/50 rounded-2xl shadow-2xl p-10 space-y-8">

          <div className="space-y-2">
            <h2 className="text-4xl font-bold text-foreground">Konto erstellen</h2>
            <p className="text-lg text-muted-foreground">Wähle einen Benutzernamen und ein Passwort.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="flex items-center gap-3 rounded-xl bg-destructive/10 border border-destructive/20 px-5 py-4 text-base text-destructive">
                <AlertCircle className="w-5 h-5 shrink-0" />
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-lg font-semibold text-foreground" htmlFor="username">
                Benutzername
              </label>
              <Input
                id="username"
                type="text"
                placeholder="dein.name"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                className="h-14 text-lg px-4 rounded-xl"
              />
            </div>

            <div className="space-y-2">
              <label className="text-lg font-semibold text-foreground" htmlFor="password">
                Passwort
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
                className="h-14 text-lg px-4 rounded-xl"
              />
            </div>

            <div className="space-y-2">
              <label className="text-lg font-semibold text-foreground" htmlFor="confirm">
                Passwort bestätigen
              </label>
              <Input
                id="confirm"
                type="password"
                placeholder="••••••••"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                autoComplete="new-password"
                className="h-14 text-lg px-4 rounded-xl"
              />
            </div>

            <Button
              type="submit"
              className="w-full h-14 text-lg font-semibold gradient-brand text-white border-0 hover:opacity-90 transition-opacity rounded-xl"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Konto wird erstellt…
                </>
              ) : (
                "Registrieren"
              )}
            </Button>

            <p className="text-lg text-muted-foreground text-center">
              Bereits registriert?{" "}
              <Link href="/login" className="text-primary font-semibold hover:underline">
                Anmelden
              </Link>
            </p>
          </form>
        </div>
      </div>
    </main>
  );
}
