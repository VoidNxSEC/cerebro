import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 18321,
    host: true,
    allowedHosts: true,
    watch: {
      ignored: [
        '**/node_modules/**',
        '**/.venv/**',
        '**/dist/**',
        '**/.git/**',
        '**/data/**',
        '**/__pycache__/**',
      ],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8009',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ws': {
        target: 'ws://localhost:8009',
        ws: true,
      },
    },
  },
})
