import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import * as api from "../api/interviewApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On page load: if a saved token exists, ask the backend who it belongs to.
  useEffect(() => {
    let cancelled = false;
    async function restore() {
      if (!api.getToken()) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.getMe();
        if (!cancelled) setUser(me);
      } catch {
        // Invalid token is cleared inside the API layer. If the backend is offline, the
        // login page appears and shows the "cannot reach backend" message on submit.
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    restore();
    return () => {
      cancelled = true;
    };
  }, []);

  // The API layer fires this event when the backend answers 401 (expired session).
  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener("auth-expired", onExpired);
    return () => window.removeEventListener("auth-expired", onExpired);
  }, []);

  const login = useCallback(async (identifier, password) => {
    const data = await api.login(identifier, password);
    setUser(data.user);
  }, []);

  const register = useCallback(async (username, email, password) => {
    const data = await api.register(username, email, password);
    setUser(data.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // even if the server call fails, log out locally
    } finally {
      api.clearToken();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>.");
  return context;
}