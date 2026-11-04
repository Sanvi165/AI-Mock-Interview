import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // works with both http://localhost:5173 and http://127.0.0.1:5173
    port: 5173,
    strictPort: true,
    // The browser calls /api on this same address; Vite forwards it to the FastAPI backend.
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
});