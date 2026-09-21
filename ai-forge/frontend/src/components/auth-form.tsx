"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/services/api";
import { useAuth } from "@/store/auth";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { toast } from "./toast";
import type { User } from "@/types";
export function AuthForm({ register = false }: { register?: boolean }) {
  const router = useRouter(),
    setAuth = useAuth((s) => s.setAuth);
  const [loading, setLoading] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setLoading(true);
    try {
      const data = await api.post<any>(
        `/auth/${register ? "register" : "login"}`,
        {
          email: f.get("email"),
          password: f.get("password"),
          nickname: f.get("nickname") || undefined,
        },
      );
      const tokens = data.tokens || data;
      setAuth(data.user as User, tokens.access_token, tokens.refresh_token);
      router.push("/chat");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <main className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_top,#2e1065,#09090b_45%)] p-4">
      <form
        onSubmit={submit}
        className="w-full max-w-sm space-y-4 rounded-2xl border bg-zinc-950/80 p-7 shadow-2xl"
      >
        <h1 className="text-2xl font-bold">
          {register ? "创建账户" : "欢迎回到 AI Forge"}
        </h1>
        {register && <Input name="nickname" placeholder="昵称" />}
        <Input name="email" type="email" placeholder="邮箱" required />
        <Input
          name="password"
          type="password"
          placeholder="密码（含大小写字母和数字）"
          minLength={8}
          required
        />
        <Button className="w-full" disabled={loading}>
          {loading ? "处理中…" : register ? "注册" : "登录"}
        </Button>
        <p className="text-center text-sm text-zinc-400">
          {register ? "已有账号？" : "还没有账号？"}{" "}
          <Link
            className="text-violet-400"
            href={register ? "/login" : "/register"}
          >
            {register ? "登录" : "注册"}
          </Link>
        </p>
      </form>
    </main>
  );
}
