import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // 💡 ngrok 호스트 차단 해제
    allowedHosts: ['trustful-occultist-vaseline.ngrok-free.dev'],
    proxy: {
      '/api': {
        // 백엔드 컨테이너가 열어둔 우분투 IP와 포트
        target: 'http://210.94.222.176:8000', 
        changeOrigin: true,
      }
    },
    watch: {
      usePolling: true,
    }
  }
})