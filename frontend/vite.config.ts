import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwind from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";

export default defineConfig({
  plugins: [react(), tailwind()],
  optimizeDeps: { include: ["leafthrough/react"] },
  build: {
    rollupOptions: {
      input: {
        app: fileURLToPath(new URL("./index.html", import.meta.url)),
        lightStudy: fileURLToPath(
          new URL("./light-study/index.html", import.meta.url),
        ),
      },
    },
  },
  server: { host: "127.0.0.1", port: 5173, strictPort: true },
  test: { environment: "node", include: ["tests/**/*.test.ts"] },
});
