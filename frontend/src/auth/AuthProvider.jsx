import { useCallback, useEffect, useMemo, useState } from "react";
import { authApi, esciSso, scambiaSso } from "./api";
import { AuthContext } from "./authContext";
import { clearToken, setToken, setUnauthorizedHandler } from "./sessione";

/**
 * Who is signed in. `me` first (bearer token if stored; behind the Life gate the
 * identity arrives without one); on 401 one SSO exchange, then `me` again.
 */
async function risolviUtente() {
  try {
    return await authApi.me();
  } catch (e) {
    if (e.status !== 401) return null;
  }
  clearToken();
  const sso = await scambiaSso();
  if (!sso) return null;
  setToken(sso.access_token);
  try {
    return await authApi.me();
  } catch {
    clearToken();
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [caricando, setCaricando] = useState(true);

  const sessioneChiusa = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const logout = useCallback(async () => {
    await esciSso();
    sessioneChiusa();
  }, [sessioneChiusa]);

  // Any 401 while the page is open (expired token, revoked role) goes back to the login.
  useEffect(() => {
    setUnauthorizedHandler(sessioneChiusa);
  }, [sessioneChiusa]);

  useEffect(() => {
    let attivo = true;
    risolviUtente().then((u) => {
      if (!attivo) return;
      setUser(u);
      setCaricando(false);
    });
    return () => {
      attivo = false;
    };
  }, []);

  const login = useCallback(async (username, password) => {
    const res = await authApi.login(username, password);
    setToken(res.access_token);
    const profilo = await authApi.me();
    setUser(profilo);
    return profilo;
  }, []);

  const valore = useMemo(
    () => ({ user, caricando, login, logout }),
    [user, caricando, login, logout],
  );
  return <AuthContext.Provider value={valore}>{children}</AuthContext.Provider>;
}
