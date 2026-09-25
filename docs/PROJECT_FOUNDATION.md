# PROJECT FOUNDATION — VAULT
## Fault-Tolerant Distributed Object Storage System

**Document Version:** 1.0  
**Status:** Foundation / Pre-Implementation  
**Date:** 2026-09-26  

---

## 1. Problem Understanding

### What is Vault?

Vault is a distributed object storage system — think of it like a simplified version of Amazon S3 or Google Cloud Storage, built from scratch to demonstrate core distributed-systems engineering concepts.

A **single storage server** is simple but fragile: the disk can fail, the machine can crash, data can corrupt, and reads/writes block each other. Vault solves this by spreading data across **multiple independent storage nodes**, keeping **multiple copies (replicas)** of every object, and automatically detecting and recovering from failures.

### What Problem Does It Solve?

| Problem | Vault's Answer |
|---|---|
| Single point of failure | Replication across ≥ 3 nodes |
| Disk corruption | Checksums verified on every read |
| Node crash | Automatic replica repair |
| Network partition | Quorum-based writes; authoritative metadata |
| Concurrent writes conflict | Server-assigned monotonic versioning |
| Storage imbalance | Background rebalancing on node join/drain |
| Silent data decay | Periodic integrity scan |

### The Core Challenge

The hard part is not storing data — it is keeping data **consistent, durable, and available** across nodes that can independently fail, experience network issues, or fall behind. The system must:

- Know where every copy of every object lives.
- Detect when a copy is missing, corrupt, or stale.
- Repair the problem without human intervention.
- Never serve stale or corrupt data to clients.
- Remain available even when some nodes are down.

---

## 2. Requirements

### 2.1 Functional Requirements

**Core Storage Operations**
- `FR-01` — PUT: Store an object by key; generate a checksum; replicate to N nodes.
- `FR-02` — GET: Retrieve an object by key; verify checksum before returning.
- `FR-03` — DELETE: Mark object deleted; propagate tombstone to all replicas.
- `FR-04` — Metadata: Retrieve object metadata (version, size, checksum, replica locations) without downloading the object body.

**Replication**
- `FR-05` — Configurable replication factor (N); default N = 3.
- `FR-06` — Configurable write quorum (W); default W = 2.
- `FR-07` — Configurable read quorum (R); default R = 2.
- `FR-08` — Object must not be acknowledged as written until W replicas confirm.
- `FR-09` — Replica placement must prefer different physical nodes.

**Versioning**
- `FR-10` — Each PUT increments the object's version number (server-assigned monotonic integer).
- `FR-11` — Stale replicas (lower version) must not overwrite newer replicas.
- `FR-12` — Conditional writes (expected-version check) must be supported.

**Node Management**
- `FR-13` — Storage nodes register with the cluster and send periodic heartbeats.
- `FR-14` — Node states: HEALTHY → SUSPECTED → FAILED → RECOVERING / DRAINING.
- `FR-15` — A node can be drained (graceful removal) without losing data.
- `FR-16` — A new node can join the cluster and receive replica migrations.

**Failure Detection**
- `FR-17` — Heartbeat-based failure detection with configurable timeout.
- `FR-18` — System identifies under-replicated objects after node failure.
- `FR-19` — System does not immediately delete data on suspicion — only after confirmed failure.

**Automatic Replica Repair**
- `FR-20` — When a replica is MISSING, CORRUPT, or STALE: automatically create a replacement.
- `FR-21` — Repair state transitions: PENDING → REPAIRING → VERIFYING → DONE / FAILED.
- `FR-22` — Repair operations must be idempotent (safe to retry).
- `FR-23` — Repaired replica must be verified before being marked DURABLE.

**Corruption Detection**
- `FR-24` — Checksum computed during PUT (SHA-256).
- `FR-25` — Checksum verified on every GET.
- `FR-26` — Periodic background integrity scan verifies all stored replicas.
- `FR-27` — Corrupt replicas trigger automatic repair.

**Rebalancing**
- `FR-28` — When a node joins: migrate replicas to include the new node.
- `FR-29` — When a node drains: migrate all its replicas to healthy nodes.
- `FR-30` — Rebalancing must never delete the last surviving copy of an object.
- `FR-31` — Rebalancing must verify migrated replicas before removing originals.

**Observability**
- `FR-32` — Expose cluster status: node states, object counts, replica health.
- `FR-33` — Expose live event log: node failures, repairs, corrupt detections.
- `FR-34` — Expose repair job queue and status.

### 2.2 Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Availability | Object readable with up to N-W node failures |
| NFR-02 | Durability | No data loss unless all N replicas fail simultaneously |
| NFR-03 | Consistency | Read-your-writes within a session |
| NFR-04 | Atomicity | Partial writes must not leave corrupt state |
| NFR-05 | Integrity | Corrupt data must never be served to clients |
| NFR-06 | Idempotency | Retry-safe writes and repairs |
| NFR-07 | Configurability | N, W, R via environment variables / config file |
| NFR-08 | Observability | All state transitions logged with timestamps |
| NFR-09 | Fault injection | System must support deliberate node kill and corruption for demo |
| NFR-10 | Simplicity | Deployable locally with a single command (Docker Compose) |

---

## 3. Major Components

### 3.1 Component Map

```
CLIENT
  |
  v
[API Gateway]           ← Single entry point for all client operations
  |
  +---> [Coordinator]   ← Orchestrates PUT/GET/DELETE across nodes; enforces quorum
  |
  +---> [Metadata Service]  ← Authoritative source of object/replica/node state
  |
  +---> [Placement Service] ← Decides which nodes hold each replica
  |
  +---> [Membership / Failure Detector]  ← Heartbeats; node state machine
  |
  +---> [Storage Nodes (N)]  ← Actually store raw object data + checksums
         |
         +---> [Repair Worker]     ← Background: detects and fixes under-replicated objects
         +---> [Integrity Scanner] ← Background: verifies checksums of stored replicas
         +---> [Rebalancer]        ← Background: migrates replicas on join/drain
```

### 3.2 Component Descriptions

| Component | Responsibility |
|---|---|
| **API Gateway** | Accepts HTTP requests from clients. Routes to Coordinator. Returns responses. |
| **Coordinator** | Executes quorum logic. Sends parallel requests to storage nodes. Collects acknowledgements. |
| **Metadata Service** | Stores and serves authoritative object/replica/node metadata. Uses SQLite (embedded). |
| **Placement Service** | Given a replication factor, selects which N healthy nodes should hold a new object. Uses round-robin with load awareness. |
| **Storage Nodes** | Store object bytes on local disk. Generate and verify checksums. Return data to Coordinator on request. |
| **Membership / Failure Detector** | Receives heartbeats from nodes. Updates node state. Triggers repair when node dies. |
| **Repair Worker** | Background loop. Finds under-replicated objects. Copies data from a healthy replica to a new target node. Verifies result. |
| **Integrity Scanner** | Background loop. Reads all locally stored replicas. Verifies checksum. Marks corrupt replicas. Triggers repair. |
| **Rebalancer** | Triggered on node join/drain. Calculates target placement. Migrates replicas. Verifies. |

---

## 4. Main Workflows

### 4.1 PUT Object

```
Client  →  API Gateway  →  Coordinator
                                |
                     1. Assign object_id + version
                     2. Compute checksum
                     3. Call Placement Service → pick N healthy nodes
                     4. Send object to N nodes in parallel
                     5. Wait for W acknowledgements (write quorum)
                     6. If W acks received → commit to Metadata → return 201
                     7. If W acks not received → rollback → return 503
```

### 4.2 GET Object

```
Client  →  API Gateway  →  Coordinator
                                |
                     1. Look up object in Metadata → get replica locations
                     2. Query R replicas in parallel
                     3. Verify checksum on each response
                     4. Return first valid R response to client
                     5. If checksum mismatch → mark replica CORRUPT → trigger repair
                     6. If no quorum readable → return 503
```

### 4.3 DELETE Object

```
Client  →  API Gateway  →  Coordinator
                                |
                     1. Look up object in Metadata
                     2. Write tombstone to Metadata (soft delete)
                     3. Send DELETE to all N replica nodes
                     4. If W nodes confirm → mark object DELETED → return 200
                     5. Background cleanup removes physical files
```

### 4.4 Replica Repair

```
Trigger: Node failure / corruption detection / integrity scan result
                                |
                     1. Repair Worker identifies under-replicated object
                     2. Creates repair job (state: PENDING)
                     3. Selects healthy source replica
                     4. Selects healthy target node
                     5. Streams object from source to target (state: REPAIRING)
                     6. Target writes + generates checksum
                     7. Coordinator verifies checksum, version, size (state: VERIFYING)
                     8. Metadata updated: new replica added (state: DONE)
                     9. Object back to DURABLE
```

### 4.5 Node Failure

```
Node heartbeat missed
        |
        v
Failure Detector: HEALTHY → SUSPECTED (1 missed heartbeat)
        |
        v
After timeout: SUSPECTED → FAILED
        |
        v
Metadata Service: identify all replicas on failed node → mark MISSING
        |
        v
Repair Worker: schedule repair jobs for all under-replicated objects
        |
        v
Repair proceeds per 4.4
```

### 4.6 Corruption Detection

```
Integrity Scanner reads stored replica bytes
        |
        v
Compute checksum of bytes
        |
        v
Compare to stored expected checksum
        |
   MATCH                    MISMATCH
     |                          |
   Continue                Mark replica CORRUPT in Metadata
                               |
                          Trigger Repair Worker
                               |
                          Do not serve corrupt replica to clients
```

### 4.7 Rebalancing (Node Join)

```
New node registers with cluster
        |
        v
Placement Service recalculates optimal replica distribution
        |
        v
Rebalancer identifies objects that should have a replica on new node
        |
        v
For each such object:
  1. Copy replica from source to new node
  2. Verify checksum + version
  3. Update Metadata: add new replica
  4. If replication_factor now exceeded → remove old replica from overloaded node
        |
        v
Node reaches HEALTHY state
```

---

## 5. System Invariants

These rules must **never** be violated:

| # | Invariant |
|---|---|
| SI-01 | An object write is never acknowledged unless ≥ W replicas have durably written it. |
| SI-02 | A corrupt or stale replica is never served to a client. |
| SI-03 | The last surviving copy of an object is never deleted. |
| SI-04 | Replica repair never overwrites a newer version with an older one. |
| SI-05 | All writes to disk are atomic: temp file → fsync → rename. |
| SI-06 | Metadata is always updated after physical writes succeed, not before. |
| SI-07 | A node in SUSPECTED state continues serving reads and writes. |
| SI-08 | A node in FAILED state is excluded from new placement decisions. |
| SI-09 | Repair jobs are idempotent: running the same job twice is safe. |
| SI-10 | Tombstoned (deleted) objects are never repaired back to DURABLE. |

---

## 6. Implementation Milestones

| Phase | Title | Deliverable |
|---|---|---|
| Phase 1 | Single-node storage | PUT/GET/DELETE, checksum, atomic writes, persistent storage |
| Phase 2 | Multi-node storage | Node registration, heartbeats, placement, replication |
| Phase 3 | Metadata service | SQLite schema, object/replica/node tracking |
| Phase 4 | Quorum operations | Configurable N/W/R, parallel coordinator, quorum logic |
| Phase 5 | Versioning | Server-assigned monotonic version, conditional writes |
| Phase 6 | Failure detection | Heartbeat timeout, node state machine, under-replication detection |
| Phase 7 | Replica repair | Repair worker, state transitions, repair verification |
| Phase 8 | Corruption detection | Integrity scanner, checksum mismatch, repair trigger |
| Phase 9 | Network partition behavior | Document behavior, quorum enforcement, stale-data prevention |
| Phase 10 | Rebalancing | Node join/drain, replica migration, verification |
| Phase 11 | Dashboard & Demo | Monitoring UI, event log, fault injection, demo script |
| Phase 12 | Documentation & Presentation | README, API docs, diagrams, slides |

---

## 7. MVP vs Advanced Features

### MVP (Required for hackathon demo)

- PUT / GET / DELETE with checksum verification
- Replication across 3 storage nodes (configurable N)
- Write quorum (W = 2) enforcement
- Read quorum with checksum verification
- Node heartbeat + failure detection
- Automatic replica repair after node failure
- Manual corruption injection + automatic detection + repair
- Basic monitoring dashboard showing node health, object count, replica status, event log
- Single-command startup (Docker Compose)
- Demo script that can be run reliably in front of judges

### Advanced (Implement after MVP)

- Versioning with conditional writes (expected-version check)
- Concurrent write conflict resolution
- Node drain with graceful replica migration
- Rebalancing on new node join
- Periodic background integrity scanner
- Full repair state machine with VERIFYING step
- Detailed performance metrics (latency, throughput)

### Future (Do not block the demo)

- TLS / authentication
- Multi-bucket support
- Erasure coding (instead of full replication)
- Distributed metadata (currently embedded SQLite is sufficient)
- Cross-datacenter replication
- Object lifecycle policies (expiry, archival)

---

## 8. Workspace Inspection Summary

### What Exists

| Item | Description | Reusable? |
|---|---|---|
| `src/` | Next.js 14 personal portfolio site (Surya Gonti's portfolio) | **No** — unrelated project |
| `netspeed-checker/` | Vite + vanilla JS network speed checker tool | **No** — unrelated project |
| `package.json` | Portfolio dependencies: Next.js, Tailwind, Zustand, Three.js | **Partially** — Next.js + Tailwind + Zustand can be reused for dashboard UI |
| `tailwind.config.js` | Tailwind configuration | **Yes** — reuse for dashboard |
| `tsconfig.json` | TypeScript config | **Yes** — reuse |

### What Must Be Created

- `vault/` — entire Vault project (separate from portfolio)
  - Backend: Node.js (Express) or Python (FastAPI) — **Decision Required** (see below)
  - Storage nodes: separate Node.js processes or Python processes
  - Metadata: SQLite (embedded, simple, reliable)
  - Dashboard frontend: Next.js (already in workspace) or simple HTML
  - Docker Compose: for multi-node local deployment

### Design Decision Required — Backend Language

The workspace has a Next.js (TypeScript) frontend already set up. Two reasonable backend options:

**Option A: Node.js + TypeScript (Express/Fastify)**
- Pro: Same language as frontend, easier integration, TypeScript type safety
- Pro: Can simulate storage nodes as separate processes in the same language
- Con: Node.js single-threaded model requires careful async I/O handling

**Option B: Python (FastAPI)**
- Pro: Excellent for I/O-heavy distributed systems
- Pro: Easy subprocess management for storage nodes
- Con: Mixed language stack (TS frontend + Python backend)

**Recommendation: Node.js + TypeScript** — keeps the entire stack in one language, matches existing workspace tooling, and TypeScript's strict typing helps enforce the complex state machines.

---

## 9. Technology Stack (Recommended)

| Layer | Technology | Reason |
|---|---|---|
| API Gateway + Coordinator | Node.js + Express + TypeScript | Fast async I/O, type-safe, matches existing workspace |
| Storage Nodes | Node.js + Express + TypeScript | Same codebase, different process/port per node |
| Metadata Service | SQLite via `better-sqlite3` | Embedded, zero-config, reliable, sufficient for hackathon scale |
| Checksum | Node.js `crypto` (SHA-256) | Built-in, fast, no external dependency |
| Atomic Writes | `tmp-file → fsync → rename` pattern | Prevents partial write corruption |
| Dashboard Frontend | Next.js + Tailwind CSS (existing) | Already configured in workspace |
| Real-time Events | Server-Sent Events (SSE) | Simple, no WebSocket overhead |
| Deployment | Docker + Docker Compose | Single command multi-node startup |
| Testing | Jest + Supertest | Standard Node.js testing |

---

## 10. Project Structure

```
vault/
├── gateway/              # API Gateway — Express server, client-facing
│   ├── src/
│   │   ├── routes/       # PUT, GET, DELETE, metadata, admin
│   │   ├── coordinator.ts # Quorum logic, parallel node requests
│   │   └── index.ts
│   └── package.json
│
├── metadata/             # Metadata Service — SQLite, object/replica/node state
│   ├── src/
│   │   ├── db.ts         # Database connection + migrations
│   │   ├── models/       # Object, Replica, Node, RepairJob models
│   │   └── service.ts    # Metadata service interface
│   └── package.json
│
├── storage/              # Storage Node — stores actual object bytes
│   ├── src/
│   │   ├── store.ts      # Read/write/delete physical files
│   │   ├── checksum.ts   # SHA-256 generation + verification
│   │   ├── scanner.ts    # Integrity scanner (background)
│   │   └── index.ts      # Express server for each node
│   └── package.json
│
├── membership/           # Failure Detector — heartbeat tracking, node state machine
│   ├── src/
│   │   └── detector.ts
│
├── repair/               # Repair Worker — finds and fixes under-replicated objects
│   ├── src/
│   │   └── worker.ts
│
├── rebalancer/           # Rebalancer — node join/drain logic
│   ├── src/
│   │   └── rebalancer.ts
│
├── common/               # Shared types, constants, utilities
│   ├── src/
│   │   ├── types.ts
│   │   └── config.ts
│
├── dashboard/            # Monitoring dashboard (Next.js, reusing existing)
│   └── (Next.js pages for cluster status, events, operations)
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fault-injection/
│
├── docs/
│   ├── PROJECT_FOUNDATION.md  ← this file
│   ├── ARCHITECTURE.md
│   ├── DATABASE_DESIGN.md
│   ├── API.md
│   ├── TESTING.md
│   ├── DEMO.md
│   └── diagrams/
│
├── scripts/
│   ├── start-cluster.sh       # Start 1 gateway + 3 storage nodes
│   ├── inject-failure.sh      # Kill a node for demo
│   └── inject-corruption.sh   # Corrupt a replica file for demo
│
├── docker/
│   ├── Dockerfile.gateway
│   ├── Dockerfile.storage
│   └── docker-compose.yml
│
└── README.md
```

---

## 11. Implementation Roadmap

| Week/Day | Phase | Tasks |
|---|---|---|
| Day 1 | Phase 1 + 2 | Single-node PUT/GET/DELETE + checksum. Then add 3-node replication. |
| Day 2 | Phase 3 + 4 | SQLite metadata service + Quorum coordinator (W=2, R=2). |
| Day 3 | Phase 5 + 6 | Versioning + Failure detection + node state machine. |
| Day 4 | Phase 7 + 8 | Repair worker + corruption detection + integrity scanner. |
| Day 5 | Phase 10 + 11 | Rebalancing + Dashboard + Docker Compose + Demo script. |
| Day 6 | Phase 12 | Testing, documentation, diagrams, presentation slides. |

---

## 12. Risks and Challenges

| Risk | Likelihood | Mitigation |
|---|---|---|
| SQLite locking under concurrent writes | Medium | Use WAL mode; serialize metadata writes |
| Repair loop overwhelming the cluster | Low | Rate-limit repair jobs; configurable concurrency |
| Demo instability (process crashes mid-demo) | Medium | Use Docker Compose with restart policies; practice demo script |
| Quorum edge cases (W > N, R + W < N + 1) | Medium | Validate config at startup; enforce R + W > N invariant |
| Network simulation on local machine | Low | Use localhost ports for "nodes"; use `tc` or manual delays for partition simulation |
| Over-engineering | High | Strict MVP discipline; implement advanced features only after core demo works |
| Atomic write on Windows | Low | Use `tmp → rename` pattern; test on Windows explicitly |

---

*End of PROJECT_FOUNDATION.md*
