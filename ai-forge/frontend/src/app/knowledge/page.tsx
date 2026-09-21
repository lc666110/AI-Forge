"use client";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Database, Plus } from "lucide-react";
import { Shell } from "@/components/shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/toast";
import { api } from "@/services/api";
import type { KnowledgeBase } from "@/types";
export default function Page() {
  const [items, setItems] = useState<KnowledgeBase[]>([]),
    [show, setShow] = useState(false);
  const load = () =>
    api
      .get<KnowledgeBase[]>("/knowledge-bases")
      .then(setItems)
      .catch((e) => toast.error(e.message));
  useEffect(() => {
    load();
  }, []);
  async function create(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    await api.post("/knowledge-bases", {
      name: f.get("name"),
      description: f.get("description"),
    });
    setShow(false);
    load();
  }
  return (
    <Shell>
      <main className="mx-auto max-w-6xl p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">知识库</h1>
            <p className="text-zinc-400">上传资料并进行可溯源问答</p>
          </div>
          <Button onClick={() => setShow(!show)}>
            <Plus className="mr-2 inline" size={18} />
            新建
          </Button>
        </div>
        {show && (
          <form
            onSubmit={create}
            className="mb-6 grid gap-3 rounded-xl border p-4"
          >
            <Input name="name" placeholder="知识库名称" required />
            <Input name="description" placeholder="描述" />
            <Button>创建</Button>
          </form>
        )}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((k) => (
            <Link
              key={k.id}
              href={`/knowledge/${k.id}`}
              className="rounded-xl border bg-zinc-950 p-5 transition hover:border-violet-500"
            >
              <Database className="mb-4 text-violet-400" />
              <h2 className="font-semibold">{k.name}</h2>
              <p className="mt-1 text-sm text-zinc-400">
                {k.description || "暂无描述"}
              </p>
            </Link>
          ))}
        </div>
      </main>
    </Shell>
  );
}
