/**
 * Every page path of the portal, in one place: router and menu read from here.
 * No page path may start with the backend prefix `/api` (the proxy would swallow it).
 */
export const PERCORSI = {
  panoramica: "/",
  aree: "/aree",
  editor: "/editor",
  guida: "/guida",
};

/** Path relative to the layout route, as <Route path> wants it. */
export const relativo = (percorso) => percorso.replace(/^\//, "");
