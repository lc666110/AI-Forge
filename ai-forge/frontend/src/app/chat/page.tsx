"use client";
import { useEffect, useState } from "react";
import { MessageSquarePlus, Pencil, Trash2 } from "lucide-react";
import { Shell } from "@/components/shell";
import { ChatPanel } from "@/components/chat-panel";
import { Button } from "@/components/ui/button";
import { api } from "@/services/api";
import { toast } from "@/components/toast";
import type { Conversation, Message } from "@/types";
export default function Page() {
  const [items, setItems] = useState<Conversation[]>([]),
    [active, setActive] = useState<number>(),
    [messages, setMessages] = useState<Message[]>([]);
  async function load() {
    try {
      const rows = await api.get<Conversation[]>("/conversations");
      setItems(rows);
    } catch (e) {
      toast.error((e as Error).message);
    }
  }
  useEffect(() => {
    let cancelled = false;
    async function loadInitial() {
      try {
        const rows = await api.get<Conversation[]>("/conversations");
        if (cancelled) return;
        setItems(rows);
        if (rows[0]) {
          const history = await api.get<Message[]>(
            `/conversations/${rows[0].id}/messages`,
          );
          if (cancelled) return;
          setMessages(history);
          setActive(rows[0].id);
        }
      } catch (e) {
        if (!cancelled) toast.error((e as Error).message);
      }
    }
    void loadInitial();
    return () => {
      cancelled = true;
    };
  }, []);
  async function select(id: number) {
    const history = await api.get<Message[]>(`/conversations/${id}/messages`);
    setMessages(history);
    setActive(id);
  }
  async function create() {
    const item = await api.post<Conversation>("/conversations", {
      title: "新对话",
      model_type: "gpt-4o",
    });
    setItems((x) => [item, ...x]);
    setActive(item.id);
    setMessages([]);
  }
  async function rename(c: Conversation) {
    const title = prompt("新标题", c.title);
    if (title) {
      await api.patch(`/conversations/${c.id}`, { title });
      load();
    }
  }
  async function remove(id: number) {
    if (confirm("确认删除此会话？")) {
      await api.delete(`/conversations/${id}`);
      setActive(undefined);
      setMessages([]);
      load();
    }
  }
  async function changeModel(model_type: string) {
    if (!active) return;
    await api.patch(`/conversations/${active}/model`, { model_type });
    setItems((x) => x.map((c) => (c.id === active ? { ...c, model_type } : c)));
    toast.success("模型已切换");
  }
  const current = items.find((x) => x.id === active);
  return (
    <Shell>
      <main className="flex h-[calc(100vh-4rem)]">
        <aside className="hidden w-72 shrink-0 border-r p-3 md:block">
          <Button
            onClick={create}
            className="mb-3 flex w-full items-center justify-center gap-2"
          >
            <MessageSquarePlus size={18} />
            新建对话
          </Button>
          <div className="space-y-1">
            {items.map((c) => (
              <div
                key={c.id}
                className={`group flex items-center rounded-lg ${active === c.id ? "bg-zinc-800" : "hover:bg-zinc-900"}`}
              >
                <button
                  onClick={() => select(c.id)}
                  className="min-w-0 flex-1 truncate p-3 text-left text-sm"
                >
                  {c.title}
                </button>
                <button
                  onClick={() => rename(c)}
                  className="hidden p-1 group-hover:block"
                >
                  <Pencil size={14} />
                </button>
                <button
                  onClick={() => remove(c.id)}
                  className="hidden p-2 group-hover:block"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </aside>
        <div className="flex min-w-0 flex-1 flex-col">
          {active && (
            <div className="flex h-12 items-center justify-end border-b px-4">
              <select
                value={current?.model_type || "gpt-4o"}
                onChange={(e) => changeModel(e.target.value)}
                className="rounded-lg border px-2 py-1 text-sm"
              >
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-5.6">GPT-5.6</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="deepseek-v4-pro">DeepSeek-V4 Pro</option>
                <option value="deepseek-flash">DeepSeek Flash</option>
                <option value="qwen-plus">通义千问 Plus</option>
              </select>
            </div>
          )}
          {active ? (
            <ChatPanel
              key={active}
              conversationId={active}
              initial={messages}
            />
          ) : (
            <div className="grid flex-1 place-items-center">
              <Button onClick={create}>创建第一个对话</Button>
            </div>
          )}
        </div>
      </main>
    </Shell>
  );
}
