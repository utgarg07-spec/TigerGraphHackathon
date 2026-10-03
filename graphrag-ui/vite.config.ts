import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: "three-encoding-shim",
      transform(code, id) {
        if (id.includes("three.module.js") && !code.includes("LinearEncoding")) {
          return {
            code: code + "\nexport const LinearEncoding = 3000;\nexport const sRGBEncoding = 3001;\n",
            map: null,
          };
        }
      },
    },
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/ui': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
      '^/[^/]+/graphrag/.*': 'http://localhost:8000',
    }
  },
});
