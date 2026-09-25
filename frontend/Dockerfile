# syntax=docker/dockerfile:1.6

# ---------- Stage 1: build ----------
FROM node:20-alpine AS build

WORKDIR /app

# Install deps first (cached unless package.json changes).
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build.
COPY . .
RUN npm run build

# ---------- Stage 2: serve ----------
FROM nginx:alpine

# Custom nginx config that supports SPA routing (falls back to index.html).
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from the build stage.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80


HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
