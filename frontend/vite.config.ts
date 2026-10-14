import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    entries: ["src/main.tsx"],
    include: ["cookie", "set-cookie-parser"],
    exclude: ["react-router", "react-router-dom"],
  },
  server: {
    port: 5173,
  },
});
