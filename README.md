# Vault — Distributed Object Storage System

> **Hackathon Project** — A fault-tolerant distributed object storage system that stores, replicates, retrieves, and automatically repairs data across multiple independent storage nodes.

---

## What Is Vault?

Vault is a simplified but technically credible version of Amazon S3, built from scratch in Node.js + TypeScript. It demonstrates core distributed-systems concepts including:

- Object storage with SHA-256 integrity verification
- Configurable replication (N=3 by default)
- Quorum-based reads and writes (W=2, R=2)
- Automatic failure detection via heartbeats
- Automatic replica repair after node failure
- Corruption detection and repair
- Node drain with graceful replica migration

---

## Architecture

```
CLIENT
  │
  ▼
┌──────────────────────────────────────┐
│            API GATEWAY               │  :8080
│  ┌─────────────┐ ┌─────────────────┐ │
│  │ Coordinator │ │ Failure Detector│ │
│  │  (Quorum)   │ │ (Heartbeats)    │ │
│  └─────────────┘ └─────────────────┘ │
│  ┌─────────────┐ ┌─────────────────┐ │
│  │Repair Worker│ │  Rebalancer     │ │
│  │ (Background)│ │  (Background)   │ │
│  └─────────────┘ └─────────────────┘ │
│          │                           │
│  ┌───────────────┐                   │
│  │ MetadataService│                  │
│  │   (SQLite)    │                   │
│  └───────────────┘                   │
└──────────────────────────────────────┘
          │
     ─────┴──────
    │      │      │
    ▼      ▼      ▼
 Node-1  Node-2  Node-3
 :8081   :8082   :8083
```

The **gateway** is the single entry point. It manages all metadata, runs background services (failure detector, repair worker), and coordinates quorum operations.

**Storage nodes** are simple HTTP servers that store raw bytes. They register with the gateway, send heartbeats, and run an integrity scanner.

---

## Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Gateway + Coordinator | Node.js + Express + TypeScript | Async I/O, type safety, same language end-to-end |
| Storage Nodes | Node.js + Express + TypeScript | Same codebase, different config per node |
| Metadata | SQLite + `better-sqlite3` | Embedded, ACID, zero-config, WAL mode for concurrency |
| Checksum | Node.js `crypto` (SHA-256) | Built-in, no extra dependency |
| Atomic Writes | `tmp → fsync → rename` | Prevents partial-write corruption |
| Dashboard | (coming) Next.js + Tailwind | Already in workspace |
| Deployment | Docker + Docker Compose | Single command multi-node startup |
| Testing | Jest + ts-jest | Standard Node.js testing |

---

## Prerequisites

- Node.js 20+
- npm 10+
- Docker + Docker Compose (for containerized deployment)

---

## Installation

```bash
cd vault
npm install
```

---

## Configuration

All settings are loaded from environment variables. Defaults are sensible for local development.

| Variable | Default | Description |
|---|---|---|
| `REPLICATION_FACTOR` | `3` | Number of replicas per object |
| `WRITE_QUORUM` | `2` | Minimum acks for a write to succeed |
| `READ_QUORUM` | `2` | Minimum reads to satisfy a GET |
| `HEARTBEAT_INTERVAL` | `5000` | Heartbeat period (ms) |
| `HEARTBEAT_TIMEOUT` | `15000` | Time before a node is marked SUSPECTED/FAILED |
| `REPAIR_INTERVAL` | `10000` | How often the repair worker runs (ms) |
| `SCAN_INTERVAL` | `60000` | How often the integrity scanner runs (ms) |
| `METADATA_DATABASE` | `./vault.db` | SQLite database path |
| `GATEWAY_PORT` | `8080` | Gateway HTTP port |
| `NODE_ID` | `node-1` | Storage node identifier |
| `NODE_PORT` | `8081` | Storage node HTTP port |
| `NODE_ADDRESS` | `localhost` | Address advertised to gateway |
| `STORAGE_PATH` | `./data` | Directory for object files |
| `GATEWAY_ADDRESS` | `localhost` | Gateway host (used by storage nodes) |

**Consistency invariant**: `R + W > N` (2 + 2 > 3) — ensures reads always see the latest write.

---

## Running Locally

### Option 1: Docker Compose (recommended)

```bash
cd vault/docker
docker compose up
```

This starts:
- Gateway on port `8080`
- Node-1 on port `8081`
- Node-2 on port `8082`
- Node-3 on port `8083`

### Option 2: PowerShell (without Docker)

```powershell
cd vault
.\scripts\start-cluster.ps1
```

### Option 3: Manual (4 terminals)

**Terminal 1 — Gateway:**
```bash
GATEWAY_PORT=8080 METADATA_DATABASE=./data/vault.db npx tsx src/gateway/index.ts
```

**Terminal 2 — Node 1:**
```bash
NODE_ID=node-1 NODE_PORT=8081 STORAGE_PATH=./data/node-1 npx tsx src/storage/index.ts
```

**Terminal 3 — Node 2:**
```bash
NODE_ID=node-2 NODE_PORT=8082 STORAGE_PATH=./data/node-2 npx tsx src/storage/index.ts
```

**Terminal 4 — Node 3:**
```bash
NODE_ID=node-3 NODE_PORT=8083 STORAGE_PATH=./data/node-3 npx tsx src/storage/index.ts
```

---

## API Examples

### Store an object
```bash
curl -X PUT http://localhost:8080/objects/reports/q1.pdf \
  -H "Content-Type: application/octet-stream" \
  --data-binary @q1.pdf
```

Response:
```json
{
  "object_id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "reports/q1.pdf",
  "version": 1,
  "size": 204800,
  "checksum": "sha256:a1b2c3...",
  "state": "DURABLE",
  "replicas": [
    { "replica_id": "...", "node_id": "node-1", "state": "HEALTHY" },
    { "replica_id": "...", "node_id": "node-2", "state": "HEALTHY" },
    { "replica_id": "...", "node_id": "node-3", "state": "HEALTHY" }
  ]
}
```

### Retrieve an object
```bash
curl http://localhost:8080/objects/reports/q1.pdf -o q1-retrieved.pdf
```

Headers returned:
```
X-Object-Version: 1
X-Object-Checksum: sha256:a1b2c3...
```

### Get object metadata (without downloading)
```bash
curl http://localhost:8080/objects/reports/q1.pdf/metadata
```

### Delete an object
```bash
curl -X DELETE http://localhost:8080/objects/reports/q1.pdf
```

### Check cluster status
```bash
curl http://localhost:8080/cluster/status
```

### List nodes
```bash
curl http://localhost:8080/nodes
```

### Drain a node
```bash
curl -X POST http://localhost:8080/nodes/node-2/drain
```

### Trigger repair manually
```bash
curl -X POST http://localhost:8080/repairs/trigger
```

### Inject corruption (demo)
```bash
curl -X POST "http://localhost:8080/admin/corrupt/node-1/OBJECT_ID"
```

### Subscribe to live events (SSE)
```bash
curl http://localhost:8080/cluster/events/stream
```

---

## Testing

```bash
# All tests
npm test

# Unit tests only
npm run test:unit

# Integration tests (requires running cluster)
npm run test:integration
```

---

## Demo

Run the automated demo script:
```powershell
.\scripts\demo.ps1
```

Or follow the [manual demo guide](docs/DEMO.md).

---

## Known Limitations

- SQLite is single-writer — sufficient for hackathon scale, not for production millions-of-TPS
- Rebalancing migrates a maximum of 10 objects on join to avoid overwhelming the cluster
- Partition tolerance: the gateway is a single point of coordination; a gateway failure stops writes (metadata is safe in SQLite)
- Scan interval is configurable but defaults to 60s — may miss corruption for up to 60s
- `X-Expected-Version` conditional writes protect against concurrent write conflicts at the gateway level

---

## Project Structure

```
vault/
├── src/
│   ├── common/          # Shared types and config
│   ├── metadata/        # SQLite metadata service
│   ├── storage/         # Storage node (file I/O + scanner)
│   ├── gateway/         # API gateway + coordinator + routes
│   ├── membership/      # Failure detector
│   ├── repair/          # Repair worker
│   └── rebalancer/      # Node join/drain rebalancer
├── tests/
│   ├── unit/            # Fast, no server required
│   └── integration/     # Require running cluster
├── docs/                # Architecture, API, and design docs
├── scripts/             # Start, demo, and fault injection
└── docker/              # Dockerfiles + docker-compose.yml
```
