"use client";

import { Bot, Database, LogOut, Settings, Shield } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/store/auth";

export function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const clearAuth = useAuth((state) => state.logout);

  function logout() {
    clearAuth();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen">
      <header className="flex h-16 items-center justify-between border-b px-5">
        <Link
          href="/chat"
          className="flex items-center gap-2 text-lg font-bold"
        >
          <Bot className="text-violet-400" />
          AI Forge
        </Link>
        <nav className="flex gap-4 text-sm">
          <Link href="/chat">对话</Link>
          <Link href="/knowledge">
            <Database size={18} />
          </Link>
          <Link href="/settings">
            <Settings size={18} />
          </Link>
          <Link href="/admin">
            <Shield size={18} />
          </Link>
          <button onClick={logout} aria-label="退出登录">
            <LogOut size={18} />
          </button>
        </nav>
      </header>
      {children}
    </div>
  );
}
