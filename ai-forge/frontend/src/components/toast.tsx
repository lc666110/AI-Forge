"use client";
import { create } from "zustand";
import { X } from "lucide-react";
type Toast = { id: number; text: string; error?: boolean };
const useToasts = create<{
  items: Toast[];
  push: (text: string, error?: boolean) => void;
  remove: (id: number) => void;
}>((set) => ({
  items: [],
  push: (text, error) => {
    const id = Date.now();
    set((s) => ({ items: [...s.items, { id, text, error }] }));
    setTimeout(
      () => set((s) => ({ items: s.items.filter((x) => x.id !== id) })),
      3500,
    );
  },
  remove: (id) => set((s) => ({ items: s.items.filter((x) => x.id !== id) })),
}));
export const toast = {
  success: (s: string) => useToasts.getState().push(s),
  error: (s: string) => useToasts.getState().push(s, true),
};
export function Toaster() {
  const { items, remove } = useToasts();
  return (
    <div className="fixed right-4 top-4 z-50 space-y-2">
      {items.map((x) => (
        <div
          key={x.id}
          className={`flex min-w-72 items-center justify-between rounded-lg border p-3 shadow-xl ${x.error ? "bg-red-950" : "bg-zinc-900"}`}
        >
          <span>{x.text}</span>
          <button onClick={() => remove(x.id)}>
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}
