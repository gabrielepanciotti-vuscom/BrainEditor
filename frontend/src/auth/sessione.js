// Session token. sessionStorage, not localStorage: a JWT cannot be revoked client side,
// so its life is bound to the browser tab (same choice as the other portals).
const TOKEN_KEY = "braineditor_token";

export function getToken() {
  try {
    return window.sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    window.sessionStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* storage unavailable: the session lasts until the page reloads */
  }
}

export function clearToken() {
  try {
    window.sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

// Whoever must react to a 401 anywhere in the page (AuthProvider -> logout) registers here.
let onUnauthorized = () => {};
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}
export const notificaNonAutorizzato = () => onUnauthorized();
