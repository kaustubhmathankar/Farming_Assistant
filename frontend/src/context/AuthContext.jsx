import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api, clearToken, getToken, setToken } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(getToken()));

  const signIn = useCallback(async (credentials, mode = "login") => {
    const data = mode === "register" ? await api.register(credentials) : await api.login(credentials);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const signOut = useCallback(async () => {
    try { if (getToken()) await api.logout(); } catch { /* token may already be expired */ }
    clearToken();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!getToken()) { setLoading(false); return null; }
    try {
      const data = await api.me();
      setUser(data);
      return data;
    } catch {
      clearToken();
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refreshUser(); }, [refreshUser]);

  const value = useMemo(() => ({ user, loading, signIn, signOut, refreshUser, isAuthenticated: Boolean(user), isAdmin: user?.role === "admin" }), [user, loading, signIn, signOut, refreshUser]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() { return useContext(AuthContext); }
