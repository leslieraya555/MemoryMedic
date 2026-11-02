import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// MemoryMedic AI 2.0 — React Frontend Configuration
// Connects the React dashboard to the FastAPI backend.

export default defineConfig({
  plugins: [react()],

  server: {
    // Local development server
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,

    // Forward API requests to the Python backend
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },

      '/health': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
});
