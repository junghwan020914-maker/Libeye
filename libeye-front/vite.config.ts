import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // Docker 외부에서 접근 가능하도록 설정
    port: 5173,
    watch: {
      usePolling: true, // 파일 변경 감지 강제 (Docker 환경 필수)
    }
  }
})
