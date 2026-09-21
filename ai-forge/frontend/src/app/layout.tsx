import "./globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/toast";
export const metadata = { title: "AI Forge", description: "AI 全栈开发脚手架" };
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="dark">
      <body>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
