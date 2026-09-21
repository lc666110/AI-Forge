"use client";
import { FormEvent, useState } from "react";
import { KeyRound } from "lucide-react";
import { Shell } from "@/components/shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/services/api";
import { toast } from "@/components/toast";
export default function Page() {
  const [busy, setBusy] = useState(false);
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget,
      f = new FormData(form),
      body = Object.fromEntries(Array.from(f.entries()).filter(([, v]) => v));
    setBusy(true);
    try {
      await api.put("/users/me/keys", body);
      toast.success("密钥已加密保存");
      form.reset();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Shell>
      <main className="mx-auto max-w-2xl p-6">
        <div className="mb-6">
          <KeyRound className="mb-3 text-violet-400" />
          <h1 className="text-2xl font-bold">模型设置</h1>
          <p className="text-zinc-400">
            密钥经服务端加密后保存，留空不会覆盖已有配置。
          </p>
        </div>
        <form onSubmit={save} className="space-y-4 rounded-xl border p-5">
          <label className="block text-sm">
            OpenAI API Key
            <Input
              className="mt-2"
              name="openai_api_key"
              type="password"
              placeholder="sk-…"
            />
          </label>
          <label className="block text-sm">
            DeepSeek API Key
            <Input className="mt-2" name="deepseek_api_key" type="password" />
          </label>
          <label className="block text-sm">
            通义千问 API Key
            <Input className="mt-2" name="qwen_api_key" type="password" />
          </label>
          <Button disabled={busy}>{busy ? "保存中…" : "保存设置"}</Button>
        </form>
      </main>
    </Shell>
  );
}
