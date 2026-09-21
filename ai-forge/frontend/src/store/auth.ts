import { create } from "zustand";

import type { User } from "@/types";

type State = {
  user: User | null;
  accessToken: string | null;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
};

export const useAuth = create<State>((set) => ({
  user: null,
  accessToken:
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null,
  setAuth: (user, accessToken, refreshToken) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    document.cookie = `access_token=${accessToken}; path=/; max-age=1800; SameSite=Lax`;
    set({ user, accessToken });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    document.cookie = "access_token=; path=/; max-age=0";
    set({ user: null, accessToken: null });
  },
}));
