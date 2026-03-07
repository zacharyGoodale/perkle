import fs from 'fs'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const httpsConfig = fs.existsSync('.certs/key.pem')
  ? { key: fs.readFileSync('.certs/key.pem'), cert: fs.readFileSync('.certs/cert.pem') }
  : undefined

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    https: httpsConfig,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
