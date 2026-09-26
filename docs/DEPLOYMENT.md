# Vault Distributed Object Storage — Deployment Guide

This guide describes how to deploy the **Vault Distributed Object Storage Cluster** and its **Control Plane UI** to cloud providers and local container environments.

---

## 1. Quick 1-Click Deploy to Render (Recommended)

1. Navigate to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** &rarr; **Blueprint**.
3. Connect your repository: `https://github.com/tammannagariy-creator/VAULT`.
4. Render automatically parses [`render.yaml`](../render.yaml) and provisions:
   - **Environment**: Docker container based on Node 22 Alpine.
   - **Healthcheck**: `/health` endpoint.
   - **Persistent Storage**: 1 GB disk mounted to `/data`.
   - **Public Access**: Automatic free HTTPS URL (e.g. `https://vault-cluster.onrender.com/ui/`).

---

## 2. Deploy to Railway

1. Go to [Railway.app](https://railway.app).
2. Click **New Project** &rarr; **Deploy from GitHub repo**.
3. Select `tammannagariy-creator/VAULT`.
4. Railway automatically detects [`railway.json`](../railway.json) and [`Dockerfile`](../Dockerfile).
5. In project settings, attach a persistent Volume to `/data`.
6. Access your public domain at `/ui/`.

---

## 3. Deploy to Fly.io

Run from the repository root:
```bash
# Launch app
fly launch

# Create persistent storage for database & object replicas
fly volumes create vault_data --size 1

# Deploy
fly deploy
```

---

## 4. Multi-Container Docker Compose (Self-Hosted / VPS)

Runs 4 isolated containers (1 Gateway + 3 Storage Nodes) across a private Docker network:
```bash
docker compose -f docker/docker-compose.yml up --build -d
```

- Gateway & Control Plane: [http://localhost:8080/ui/](http://localhost:8080/ui/)
- Storage Node 1: `http://localhost:8081`
- Storage Node 2: `http://localhost:8082`
- Storage Node 3: `http://localhost:8083`

---

## 5. Universal Production Container Architecture

The root [`Dockerfile`](../Dockerfile) packages the entire cluster:
- **Supervisor**: [`scripts/cluster-runner.mjs`](../scripts/cluster-runner.mjs)
- **Processes**:
  - `Gateway` listening on dynamic cloud `$PORT` (default 8080)
  - `Node-1` listening on internal port 8081
  - `Node-2` listening on internal port 8082
  - `Node-3` listening on internal port 8083
- **Data Persistence**: `/data` directory storing SQLite metadata (`vault.db`) and replicas (`node-1/`, `node-2/`, `node-3/`).
