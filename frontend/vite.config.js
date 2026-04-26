import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: './',
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/library': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/data': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/library': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/data': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
