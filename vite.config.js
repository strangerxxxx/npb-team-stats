import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function publicBase() {
  const raw = process.env.BASE_PATH;
  if (!raw) return "/";
  return raw.endsWith("/") ? raw : `${raw}/`;
}

export default defineConfig({
  base: publicBase(),
  plugins: [react()],
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: "recharts", test: /[\\/]node_modules[\\/]recharts[\\/]/ },
            {
              name: "react",
              test: /[\\/]node_modules[\\/](react-dom|react)[\\/]/,
            },
            { name: "vendor", test: /[\\/]node_modules[\\/]/ },
          ],
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
  },
});
