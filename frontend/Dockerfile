# ---------- Stage 1: build the static bundle with Vite ----------
FROM node:22-alpine AS build

WORKDIR /app

# Copy dependency manifests first to leverage layer caching
COPY package.json package-lock.json ./

# Install exactly what package-lock.json pins
RUN npm ci

# Copy the source code and build the production bundle into /app/dist
COPY . .
RUN npm run build


# ---------- Stage 2: serve the bundle with nginx ----------
FROM nginx:1.28-alpine

# Backend base URL used by the /api reverse proxy (no trailing slash).
# Docker Compose: service name. Kubernetes: override it via ConfigMap with the FQDN,
# e.g. http://backend-service.<namespace>.svc.cluster.local:5000
# (nginx's resolver ignores the search domains in /etc/resolv.conf).
ENV BACKEND_URL=http://backend:5000

# Let the entrypoint export the container's DNS servers as NGINX_LOCAL_RESOLVERS
ENV NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1

# The official nginx image runs envsubst on /etc/nginx/templates/*.template
# at startup and writes the result to /etc/nginx/conf.d/
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template

# Only the compiled static files reach the final image (no Node, no node_modules)
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# Mark the container unhealthy if nginx stops serving the app
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q --spider http://127.0.0.1/ || exit 1
