import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { clearTokens, getTokens, refreshAccessToken } from "../api/client";
import { loadCurrentUser, login, logout, requestPasswordReset, signup } from "../api/auth";
import type { AuthPayload, Profile, User } from "../types";

type AuthContextValue = {
  initialized: boolean;
  isAuthenticated: boolean;
  user: User | null;
  profile: Profile | null;
  signIn: (email: string, password: string) => Promise<AuthPayload>;
  signUp: (payload: { email: string; password: string; display_name: string }) => Promise<AuthPayload>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ detail: string; email_exists: boolean }>;
  reload: () => Promise<void>;
  setProfile: (profile: Profile | null) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [initialized, setInitialized] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);

  async function reload() {
    const { access, refresh } = getTokens();
    const token = access || (refresh ? await refreshAccessToken() : null);
    if (!token) {
      clearTokens();
      setUser(null);
      setProfile(null);
      setInitialized(true);
      return;
    }

    try {
      const data = await loadCurrentUser();
      setUser(data.user);
      setProfile(data.profile);
    } catch {
      clearTokens();
      setUser(null);
      setProfile(null);
    } finally {
      setInitialized(true);
    }
  }

  useEffect(() => {
    void reload();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      initialized,
      isAuthenticated: Boolean(user),
      user,
      profile,
      signIn: async (email, password) => {
        const data = await login(email, password);
        setUser(data.user);
        setProfile(data.profile ?? null);
        return data;
      },
      signUp: async (payload) => {
        const data = await signup(payload);
        setUser(data.user);
        setProfile(data.profile ?? null);
        return data;
      },
      signOut: async () => {
        await logout();
        setUser(null);
        setProfile(null);
      },
      resetPassword: requestPasswordReset,
      reload,
      setProfile,
    }),
    [initialized, user, profile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
