import process from 'node:process'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Backend URL used by the dev server proxy. Override it when the API is not on
// localhost:5000, e.g. API_PROXY_TARGET=http://backend:5000 inside Docker Compose.
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:5000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      // The browser calls /api/* on the same origin (no CORS needed) and Vite
      // forwards it to Flask without the prefix: /api/rooms -> /rooms
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
