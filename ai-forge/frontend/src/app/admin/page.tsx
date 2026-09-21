"use client";
import { useEffect, useState } from "react";
import { Database, MessageSquare, Users, Waypoints } from "lucide-react";
import { Shell } from "@/components/shell";
import { api } from "@/services/api";
import { toast } from "@/components/toast";
const cards = [
  ["users", "用户数", Users],
  ["conversations", "会话数", MessageSquare],
  ["knowledge_bases", "知识库", Database],
  ["vector_chunks", "向量片段", Waypoints],
] as const;
export default function Page() {
  const [stats, setStats] = useState<Record<string, number>>({});
  useEffect(() => {
    api
      .get<Record<string, number>>("/admin/stats")
      .then(setStats)
      .catch((e) => toast.error(e.message));
  }, []);
  return (
    <Shell>
      <main className="mx-auto max-w-6xl p-6">
        <h1 className="mb-6 text-2xl font-bold">管理后台</h1>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {cards.map(([key, label, Icon]) => (
            <div key={key} className="rounded-xl border p-5">
              <Icon className="mb-4 text-violet-400" />
              <div className="text-3xl font-bold">{stats[key] ?? "—"}</div>
              <div className="text-sm text-zinc-400">{label}</div>
            </div>
          ))}
        </div>
      </main>
    </Shell>
  );
}
