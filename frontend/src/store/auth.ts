import { create } from "zustand";
import { persist } from "zustand/middleware";

type AuthState = {
  access: string | null;
  refresh: string | null;
  username: string | null;
  setSession: (access: string, refresh: string, username: string) => void;
  clear: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      access: null,
      refresh: null,
      username: null,
      setSession: (access, refresh, username) => set({ access, refresh, username }),
      clear: () => set({ access: null, refresh: null, username: null }),
    }),
    { name: "keelnote-auth" },
  ),
);
