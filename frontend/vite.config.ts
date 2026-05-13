import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/query': 'http://localhost:8000',
      '/benchmark': 'http://localhost:8000',
      '/corpus': 'http://localhost:8000',
      '/system-info': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
