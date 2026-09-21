import * as React from "react";
import { cn } from "@/lib/utils";
export function Button({
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "rounded-lg bg-violet-600 px-4 py-2 font-medium transition hover:bg-violet-500 disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
