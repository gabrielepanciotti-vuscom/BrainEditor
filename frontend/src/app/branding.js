// Resolved branding of the tree (name + light/dark logo), written at build time next to
// suite-theme.css. Optional: without the file the node shows its own name.
const trovati = import.meta.glob("../suite-branding.json", { eager: true, import: "default" });
export const BRANDING = Object.values(trovati)[0] || null;
