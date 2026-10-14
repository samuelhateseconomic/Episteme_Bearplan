import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Production: `npm run build` writes dist/, which the FastAPI service serves on 127.0.0.1:8765.
// Development: `npm run dev` serves on 127.0.0.1:5173 and proxies /api to a running service.
// changeOrigin stays false so the service's same-origin check sees matching Host and Origin.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": { target: "http://127.0.0.1:8765", changeOrigin: false },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
});
