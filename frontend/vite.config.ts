import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Allow overriding proxy target via env (useful inside Docker)
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:5000'
console.log('[Vite] Proxy target for /api ->', proxyTarget)

export default defineConfig({
  plugins: [react()],
  resolve: { 
    alias: { 
      '@': path.resolve(__dirname, './src') 
    } 
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('[Proxy] Error:', err.message);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('[Proxy] Request:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('[Proxy] Response:', proxyRes.statusCode, req.url);
          });
        },
      }
    }
  }
})
