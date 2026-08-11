import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const backendTarget = process.env.VITE_BACKEND_TARGET || 'http://127.0.0.1:8765'

export default defineConfig({
  base: './',
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true
      },
      '/library': {
        target: backendTarget,
        changeOrigin: true
      },
      '/data': {
        target: backendTarget,
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 3000,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true
      },
      '/library': {
        target: backendTarget,
        changeOrigin: true
      },
      '/data': {
        target: backendTarget,
        changeOrigin: true
      }
    }
  }
})
