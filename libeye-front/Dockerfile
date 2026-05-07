# frontend/Dockerfile
FROM node:20-alpine

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 파일 먼저 복사 및 설치 (Docker 캐시 최적화)
COPY package*.json ./
RUN npm install

# 나머지 프로젝트 코드 복사
COPY . .

# Vite 기본 포트 노출
EXPOSE 5173

# Vite 서버 실행 (외부 접속을 허용하기 위해 --host 0.0.0.0 추가)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
