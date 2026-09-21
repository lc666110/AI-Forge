"use client";
import { FormEvent, useState } from "react";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { FileUp, Send } from "lucide-react";
import { Shell } from "@/components/shell";
import { Button } from "@/components/ui/button";
import { api, sse } from "@/services/api";
import { toast } from "@/components/toast";
type Entry = { question: string; answer: string; sources: any[] };
export default function Page() {
  const { id } = useParams<{ id: string }>();
  const [items, setItems] = useState<Entry[]>([]),
    [busy, setBusy] = useState(false);
  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setBusy(true);
    try {
      await api.post(`/knowledge-bases/${id}/documents`, form);
      toast.success("文档解析与索引完成");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function ask(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget,
      q = String(new FormData(form).get("q") || "").trim();
    if (!q) return;
    form.reset();
    setItems((x) => [...x, { question: q, answer: "", sources: [] }]);
    setBusy(true);
    try {
      await sse(
        `/knowledge-bases/${id}/chat/stream`,
        { question: q },
        (event) =>
          setItems((prev) => {
            const copy = [...prev],
              last = { ...copy.at(-1)! };
            if (event.type === "sources") last.sources = event.sources;
            if (event.type === "token") last.answer += event.content;
            copy[copy.length - 1] = last;
            return copy;
          }),
      );
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Shell>
      <main className="mx-auto flex h-[calc(100vh-4rem)] max-w-5xl flex-col p-5">
        <label className="mb-4 flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed p-4 text-zinc-400 hover:border-violet-500">
          <FileUp />
          上传 PDF / DOCX / TXT / Markdown
          <input
            type="file"
            accept=".pdf,.docx,.txt,.md,.markdown"
            className="hidden"
            onChange={upload}
          />
        </label>
        <section className="flex-1 space-y-5 overflow-y-auto">
          {items.map((x, i) => (
            <article key={i} className="space-y-2">
              <div className="ml-auto max-w-2xl rounded-xl bg-violet-600 p-3">
                {x.question}
              </div>
              <div className="max-w-3xl rounded-xl bg-zinc-900 p-4">
                <ReactMarkdown>{x.answer}</ReactMarkdown>
                {x.sources.length > 0 && (
                  <details className="mt-4 text-xs text-zinc-400">
                    <summary>引用来源（{x.sources.length}）</summary>
                    {x.sources.map((s, j) => (
                      <div key={j} className="mt-2 border-l-2 pl-2">
                        [{j + 1}] {s.document} · 片段 {s.chunk}
                        <p>{s.content}</p>
                      </div>
                    ))}
                  </details>
                )}
              </div>
            </article>
          ))}
        </section>
        <form onSubmit={ask} className="mt-4 flex gap-2">
          <textarea
            name="q"
            required
            className="min-h-12 flex-1 rounded-xl border p-3"
            placeholder="基于知识库提问…"
          />
          <Button disabled={busy}>
            <Send size={18} />
          </Button>
        </form>
      </main>
    </Shell>
  );
}
