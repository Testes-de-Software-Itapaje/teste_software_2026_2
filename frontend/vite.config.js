import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // No Docker em Windows, o volume montado não dispara eventos de arquivo;
    // o polling garante que as alterações sejam recarregadas.
    watch: { usePolling: true, interval: 300 },
  },
})
