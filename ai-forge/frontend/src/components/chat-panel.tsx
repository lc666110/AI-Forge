"use client";
import { FormEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, Send, User } from "lucide-react";
import { sse } from "@/services/api";
import { Button } from "./ui/button";
import { toast } from "./toast";
import type { Message, ToolEvent } from "@/types";
export function ChatPanel({
  conversationId,
  initial = [],
}: {
  conversationId: number;
  initial?: Message[];
}) {
  const [messages, setMessages] = useState(initial),
    [text, setText] = useState(""),
    [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  async function send(e: FormEvent) {
    e.preventDefault();
    if (!text.trim() || busy) return;
    const question = text.trim();
    setText("");
    setMessages((x) => [
      ...x,
      { role: "user", content: question },
      { role: "assistant", content: "", tools: [] },
    ]);
    setBusy(true);
    try {
      await sse(
        "/chat/stream",
        {
          conversation_id: conversationId,
          content: question,
          enable_tools: true,
        },
        (event) => {
          if (event.type === "error") throw new Error(event.message);
          setMessages((prev) => {
            const copy = [...prev],
              last = { ...copy[copy.length - 1] };
            if (event.type === "token") last.content += event.content;
            if (event.type.startsWith("tool_"))
              last.tools = [...(last.tools || []), event as ToolEvent];
            copy[copy.length - 1] = last;
            return copy;
          });
        },
      );
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="flex min-w-0 flex-1 flex-col">
      <div className="flex-1 space-y-6 overflow-y-auto p-4 md:p-8">
        {messages.length === 0 && (
          <div className="mt-24 text-center text-zinc-500">
            <Bot className="mx-auto mb-3" size={40} />
            <p>开始一次有用的对话</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`mx-auto flex max-w-3xl gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}
          >
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-zinc-800">
              {m.role === "user" ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${m.role === "user" ? "bg-violet-600" : "bg-zinc-900"}`}
            >
              <div className="prose prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {m.content}
                </ReactMarkdown>
                {busy && i === messages.length - 1 && (
                  <span className="animate-pulse">▋</span>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottom} />
      </div>
      <form onSubmit={send} className="border-t p-4">
        <div className="mx-auto flex max-w-3xl gap-2">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.ctrlKey) {
                e.preventDefault();
                e.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder="输入消息，Ctrl+Enter 换行"
            className="min-h-12 flex-1 resize-none rounded-xl border p-3 outline-none"
          />
          <Button disabled={busy || !text.trim()}>
            <Send size={18} />
          </Button>
        </div>
      </form>
    </section>
  );
}
