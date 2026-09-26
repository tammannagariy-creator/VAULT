# Production Dockerfile for Vault Distributed Object Storage
# Packages Gateway + 3 Storage Nodes + Control Plane UI in a single container
FROM node:22-alpine

# Install curl for health checks
RUN apk add --no-cache curl

WORKDIR /app

# Copy package manifests and install dependencies
COPY package*.json ./
RUN npm install

# Copy application configuration and source code
COPY tsconfig.json ./
COPY src ./src
COPY scripts ./scripts
COPY dashboard/public ./dashboard/public

# Create default data directory and permissions
RUN mkdir -p /data && chmod -R 777 /data

ENV NODE_ENV=production
ENV PORT=8080
ENV GATEWAY_PORT=8080
ENV DATA_DIR=/data

# Expose Gateway & Control Plane port
EXPOSE 8080

# Health check against Gateway health endpoint
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Launch the universal cluster supervisor
CMD ["node", "scripts/cluster-runner.mjs"]
