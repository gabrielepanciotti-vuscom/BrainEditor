import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Port 3035 / backend 8035: assigned to BrainEditor.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // The linked design-system lives outside the node: one React copy, the node's.
  resolve: { dedupe: ["react", "react-dom", "react-router-dom"] },
  server: {
    port: 3035,
    host: true,
    allowedHosts: true,
    proxy: { "^/api/": "http://localhost:8035" },
  },
  test: {
    environment: "jsdom",
    globals: true,
    server: { deps: { inline: [/\/Life\//] } },
    setupFiles: ["./src/test/setup.js"],
  },
});
