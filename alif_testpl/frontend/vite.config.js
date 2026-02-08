import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: false,
    hmr: {
      // When the app is accessed through Nginx on http://localhost (port 80),
      // the browser's location.port is empty and Vite may build an invalid WS URL.
      // Force the client to connect back via port 80.
      host: 'localhost',
      clientPort: 80,
      protocol: 'ws'
    },
    proxy: {
      '/api': {
        // In Docker Compose the backend is reachable by service name
        target: 'http://backend:5000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})