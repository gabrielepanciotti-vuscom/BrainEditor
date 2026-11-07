import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { applyTheme, loadThemePreference } from "@suite/design-system";
import "@suite/design-system/fonts.css";
import "./index.css";
import App from "./App.jsx";

// The user's remembered theme and mode, before the first render.
applyTheme(document.documentElement, loadThemePreference());

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
