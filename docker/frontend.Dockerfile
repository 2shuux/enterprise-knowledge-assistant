# ---- build stage: compile the React app ----
FROM node:20-alpine AS build
WORKDIR /app
COPY apps/frontend/package.json apps/frontend/package-lock.json* ./
RUN npm install
COPY apps/frontend/ .
RUN npm run build

# ---- runtime stage: nginx serves static files + proxies /api ----
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
