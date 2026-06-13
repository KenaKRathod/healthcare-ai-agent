import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backendTarget = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/register': backendTarget,
      '/login': backendTarget,
      '/me': backendTarget,
      '/health-data': backendTarget,
      '/health-goals': backendTarget,
      '/health-analytics': backendTarget,
      '/health-journey': backendTarget,
      '/health-report': backendTarget,
      '/health-workflow': backendTarget,
      '/upload-health-data': backendTarget,
      '/ai-health-chat': backendTarget,
      '/conversations': backendTarget,
      '/audit-logs': backendTarget,
      '/medication-schedule': backendTarget,
      '/medication-adherence': backendTarget,
      '/doctor': backendTarget,
      '/analytics': backendTarget,
    },
  },
})
