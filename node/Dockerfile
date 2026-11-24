# syntax=docker/dockerfile:1
# --- Etapa de dependencias: npm solo existe aquí
FROM node:24-slim@sha256:32e57b5784e8875d2cc0112dcaf13f9100f2d0d9446187808738e99aee29a5a2 AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts && npm cache clean --force

# --- Etapa final: distroless (sin shell, sin gestor de paquetes), usuario nonroot
FROM gcr.io/distroless/nodejs24-debian13@sha256:39b0407357c9fadf1a9708d22088f02de21f0e1e8a688474eea2d8701e7d5693
ENV NODE_ENV=production
WORKDIR /app
COPY --from=deps --chown=65532:65532 /app/node_modules ./node_modules
COPY --chown=65532:65532 server.js healthcheck.js ./
USER 65532:65532
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["/nodejs/bin/node", "healthcheck.js"]
CMD ["server.js"]
