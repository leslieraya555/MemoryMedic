
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// MemoryMedic AI 2.0
// Vite + React development configuration

export default defineConfig({
  plugins: [react()],

  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,

    proxy: {
      '/health': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },

      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
