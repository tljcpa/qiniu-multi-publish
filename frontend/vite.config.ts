import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 开发态把后端接口代理到本地 8082；生产态由 Caddy 按路径反代，前端用同源相对路径。
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/platforms": "http://127.0.0.1:8082",
      "/adapt": "http://127.0.0.1:8082",
      "/health": "http://127.0.0.1:8082",
    },
  },
});
