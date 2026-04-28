"use client";

import Link from "next/link";
import { Cloud, LogOut, User } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="w-full px-6 xl:px-8 h-20 flex items-center justify-between">
        {/* Brand */}
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="gradient-brand p-2 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
            <Cloud className="w-6 h-6 text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight text-foreground">Cloud Todo</span>
        </Link>

        {/* Right side */}
        <div className="flex items-center gap-1">
          <ThemeToggle />
        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-3 text-muted-foreground hover:text-foreground h-11 px-3">
                <div className="gradient-brand w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <span className="hidden sm:block text-base font-medium">{user.username}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-52">
              <DropdownMenuLabel className="flex items-center gap-2 text-base py-2">
                <User className="w-4 h-4 text-muted-foreground" />
                {user.username}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive cursor-pointer text-base py-2"
                onClick={logout}
              >
                <LogOut className="w-4 h-4 mr-2" />
                Abmelden
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
        </div>
      </div>
    </header>
  );
}
