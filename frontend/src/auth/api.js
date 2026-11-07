import { getToken, notificaNonAutorizzato, setToken } from "./sessione";

/**
 * Exchange of a gateway/SSO cookie for a portal token. Only the local auth provider
 * has this endpoint: 404 or a network error mean "no provider", never a failure.
 */
export async function scambiaSso() {
  try {
    const r = await fetch("/api/auth/sso/scambia", { method: "POST", credentials: "include" });
    if (!r.ok) return null;
    const dati = await r.json().catch(() => null);
    return dati?.access_token ? dati : null;
  } catch {
    return null;
  }
}

/** Best effort: ends the SSO session when the provider exists. */
export async function esciSso() {
  try {
    await fetch("/api/auth/sso/esci", { method: "POST", credentials: "include" });
  } catch {
    /* no provider or offline: the local token is dropped anyway */
  }
}

/**
 * fetch on the backend with the session token. Throws an Error with the API detail,
 * `status` and, for an invalid note, `problemi`. `silenzioso` skips the 401 handling
 * (the caller deals with it, as the startup check does).
 */
export async function chiama(url, { headers, riprova = true, silenzioso = false, ...opzioni } = {}) {
  const token = getToken();
  const r = await fetch(url, {
    ...opzioni,
    headers: {
      ...(opzioni.body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });
  const dati = await r.json().catch(() => ({}));
  if (!r.ok) {
    // Expired or revoked session: back to the login. A failed login is a 401 too,
    // and its detail is what the user must read.
    if (r.status === 401 && token && !silenzioso) {
      // Once: the SSO session may still be valid and give a fresh token.
      const sso = riprova ? await scambiaSso() : null;
      if (sso) {
        setToken(sso.access_token);
        return chiama(url, { headers, ...opzioni, riprova: false });
      }
      notificaNonAutorizzato();
    }
    const err = new Error(
      typeof dati.detail === "string"
        ? dati.detail
        : dati.detail?.messaggio || `errore ${r.status}`,
    );
    err.status = r.status;
    err.problemi = dati.detail?.problemi || [];
    throw err;
  }
  return dati;
}

export const authApi = {
  login: (login, password) =>
    chiama("/api/auth/login", { method: "POST", body: JSON.stringify({ login, password }) }),
  me: () => chiama("/api/auth/me", { silenzioso: true }),
};
