# Vault — Hackathon Presentation & Architecture Guide

## 1. Executive Summary & Problem Formulation
Traditional single-box storage systems suffer from single-point-of-failure vulnerabilities, silent bit-rot data corruption, and sudden availability drops during node maintenance or partition events.
**Vault** is a ground-up, production-grade distributed object storage system engineered to provide strong consistency and continuous durability guarantees across unreliable, independently crashing storage nodes.

---

## 2. Core Architecture & Quorum Theory

### The Quorum Invariant: `R + W > N`
Vault operates under an $N=3, W=2, R=2$ quorum policy:
- **$N=3$**: Every object is replicated across three distinct storage nodes.
- **$W=2$**: A write (PUT) is acknowledged only when at least 2 nodes confirm durable commit.
- **$R=2$**: A read (GET) queries replicas and must verify valid checksum from at least 2 nodes.

Because $R + W = 4 > 3$, the Pigeonhole Principle guarantees that any read quorum intersects with any write quorum by at least one node:
$$\text{ReadQuorum} \cap \text{WriteQuorum} \neq \emptyset$$
This guarantees that clients always observe the freshest committed version without requiring synchronous 3-node locks.

```
       [Client Request]
              │
              ▼
   ┌──────────────────────┐
   │    Vault Gateway     │ (Port 8080)
   │  - Quorum Coord.     │
   │  - Failure Detector  │
   │  - Auto-Repair Loop  │
   └──────────┬───────────┘
              │ (HTTP Parallel Dispatch)
      ┌───────┼───────┐
      ▼       ▼       ▼
   ┌──────┐┌──────┐┌──────┐
   │Node 1││Node 2││Node 3│
   │:8081 ││:8082 ││:8083 │
   └──────┘└──────┘└──────┘
```

---

## 3. High-Resiliency Subsystems

### 1. Atomic Storage Engine (`ObjectStore`)
- Writes are staged in `<objectId>.tmp` files, flushed to disk with synchronous `fsync()`, and atomically renamed to `<objectId>.dat`.
- Crashed or partial writes leave only `.tmp` remnants, which are pruned at startup before accepting traffic.

### 2. End-to-End Cryptographic Integrity & Anti-Entropy
- SHA-256 digests (`sha256:<hex>`) are calculated on stream ingress.
- Companion `.meta` sidecar files record canonical checksums and monotonic versions alongside raw data.
- **IntegrityScanner**: Periodic daemon performs background anti-entropy checks against stored blocks. Corrupted files trigger automatic self-healing via `POST /internal/corruption`.

### 3. Asymmetric Failure Detection
- Storage nodes dispatch heartbeats every $5000\text{ms}$.
- Missed heartbeats transition nodes through:
  $$\text{HEALTHY} \xrightarrow{t > 7.5s} \text{SUSPECTED} \xrightarrow{t > 15s} \text{FAILED}$$
- `SUSPECTED` nodes still satisfy active read/write quorums to mitigate transient network spikes, while `FAILED` nodes are immediately excluded from new placement.

### 4. Self-Healing & Automatic Replica Repair
- When a node transitions to `FAILED` or reports corrupted blocks, the `RepairWorker` triggers:
  1. Identifies under-replicated objects ($\text{healthy\_replicas} < N$).
  2. Selects a verified healthy source replica and an available target node.
  3. Copies object streams and verifies source and destination checksums before updating SQLite metadata.
  4. Restores object state to `DURABLE`.

### 5. Rebalancing & Graceful Draining
- Operators can decommission nodes with `POST /nodes/:id/drain`.
- Vault marks the target `DRAINING`, prevents new write allocations, and actively replicates resident blocks to other healthy nodes before shutdown.

---

## 4. Verification & Validation Summary

| Test Suite | Coverage | Status |
|---|---|---|
| `placement.test.ts` | Node capacity sorting, node exclusion, repair targets | **PASS** (100%) |
| `checksum.test.ts` | SHA-256 determinism, corruption rejection, hex extraction | **PASS** (100%) |
| `objectstore.test.ts` | Atomic tmp-rename, fsync durability, deletion, crash recovery | **PASS** (100%) |
| `metadata.test.ts` | Node state machines, object versioning, replica deduplication, events | **PASS** (100%) |
| **Total Test Count** | **45 unit tests passed** | **100% Passed** |

---

## 5. Live Demonstration Sequence

1. **Start the Cluster**: Execute `.\scripts\start-cluster.ps1` (or `docker compose up`).
2. **Execute Automated Verification**: Run `.\scripts\demo.ps1` in PowerShell.
3. **Inspect Real-Time Telemetry**: Open the Next.js Telemetry Dashboard on `http://localhost:3001` or inspect Gateway stream on `http://localhost:8080/cluster/events/stream`.
