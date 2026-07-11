import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In Docker Compose the browser hits the Vite dev server, which proxies /api to
// the backend service. VITE_API_PROXY_TARGET points at the backend container
// (http://backend:8000) in Compose and defaults to localhost for host-run dev.
const apiTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
})
