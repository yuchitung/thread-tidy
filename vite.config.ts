import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  publicDir: 'public',
  server: {
    host: 'localhost',
    port: 5173,
    strictPort: false,
    open: true
  },
  preview: {
    host: 'localhost', 
    port: 4173,
    strictPort: false,
    open: true
  }
})