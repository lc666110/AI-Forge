import * as React from "react";
import { cn } from "@/lib/utils";
export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "w-full rounded-lg border px-3 py-2 outline-none focus:ring-2 focus:ring-violet-600",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";
