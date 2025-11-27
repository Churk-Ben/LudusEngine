import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  root: path.resolve(__dirname),
  build: {
    outDir: path.resolve(__dirname, 'static'),
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('naive-ui')) {
              return 'naive-ui'
            }
            return 'vendor'
          }
        }
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/providers': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/games': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/players': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/llmol': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/llmlc': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  }
})
