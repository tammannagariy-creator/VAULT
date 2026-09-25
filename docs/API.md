# Vault — API Reference

All requests go to the **Gateway** (default: `http://localhost:8080`).

---

## Object Storage

### PUT /objects/{key}

Store an object by key. Creates the object if it doesn't exist, or updates it.

**Method:** `PUT`  
**URL:** `/objects/{key}`  
Key can include slashes: `reports/2024/q1.pdf`

**Headers:**
| Header | Required | Description |
|---|---|---|
| `Content-Type` | Yes | `application/octet-stream` |
| `X-Expected-Version` | No | Conditional write. Must match current version (0 for new objects). Returns 409 if not. |

**Body:** Raw binary data (the object bytes)

**Success Response — 201 Created (new) or 200 OK (update):**
```json
{
  "object_id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "reports/q1.pdf",
  "version": 1,
  "size": 204800,
  "checksum": "sha256:a1b2c3d4...",
  "state": "DURABLE",
  "replicas": [
    { "replica_id": "...", "node_id": "node-1", "state": "HEALTHY" },
    { "replica_id": "...", "node_id": "node-2", "state": "HEALTHY" },
    { "replica_id": "...", "node_id": "node-3", "state": "HEALTHY" }
  ]
}
```

**Error Responses:**
| Status | Reason |
|---|---|
| 400 | Empty body |
| 409 | Version conflict (X-Expected-Version mismatch) |
| 503 | No healthy nodes; or write quorum not achieved |

---

### GET /objects/{key}

Retrieve an object by key. Verifies checksum before returning.

**Method:** `GET`  
**URL:** `/objects/{key}`

**Success Response — 200 OK:**
- Body: raw object bytes
- `X-Object-Id`: object UUID
- `X-Object-Version`: current version
- `X-Object-Checksum`: `sha256:<hex>`

**Error Responses:**
| Status | Reason |
|---|---|
| 404 | Object not found |
| 503 | Read quorum not achieved |

---

### DELETE /objects/{key}

Delete an object (soft delete — tombstoned in metadata, files cleaned up).

**Method:** `DELETE`  
**URL:** `/objects/{key}`

**Success Response — 200 OK:**
```json
{
  "object_id": "550e8400-...",
  "key": "reports/q1.pdf",
  "deleted": true,
  "nodes_cleaned": 3
}
```

---

### GET /objects/{key}/metadata

Get object metadata without downloading the data.

**Method:** `GET`  
**URL:** `/objects/{key}/metadata`

**Success Response — 200 OK:**
```json
{
  "object_id": "550e8400-...",
  "logical_key": "reports/q1.pdf",
  "version": 2,
  "size": 204800,
  "checksum": "sha256:...",
  "replication_factor": 3,
  "placement_epoch": 1,
  "state": "DURABLE",
  "created_at": "2024-01-01T00:00:00.000Z",
  "updated_at": "2024-01-01T01:00:00.000Z",
  "replicas": [...]
}
```

---

## Node Management

### GET /nodes

List all registered storage nodes.

**Success Response — 200 OK:**
```json
{
  "nodes": [
    {
      "node_id": "node-1",
      "address": "localhost",
      "port": 8081,
      "state": "HEALTHY",
      "last_heartbeat": "2024-01-01T00:00:05.000Z",
      "storage_used": 1048576,
      "storage_total": 0,
      "registered_at": "2024-01-01T00:00:00.000Z"
    }
  ],
  "count": 3
}
```

---

### GET /nodes/{id}

Get a specific node with its replica count.

---

### POST /nodes/{id}/drain

Initiate graceful node drain. Marks node as DRAINING and schedules repair jobs for all its replicas.

**Success Response — 200 OK:**
```json
{
  "node_id": "node-2",
  "state": "DRAINING",
  "jobs_created": 5,
  "message": "Node node-2 is draining. 5 replicas are being migrated."
}
```

**Error Responses:**
| Status | Reason |
|---|---|
| 400 | Node already draining or insufficient nodes for quorum |
| 404 | Node not found |

---

## Cluster

### GET /cluster/status

Full cluster health snapshot.

**Success Response — 200 OK:**
```json
{
  "nodes": [...],
  "totalObjects": 42,
  "durableObjects": 40,
  "underReplicatedObjects": 2,
  "totalReplicas": 126,
  "healthyReplicas": 122,
  "corruptReplicas": 0,
  "pendingRepairJobs": 2,
  "recentEvents": [...]
}
```

---

### GET /cluster/events

Recent event log (last 50 by default).

**Query Params:** `?limit=100` (max 200)

---

### GET /cluster/events/stream

Server-Sent Events stream for live dashboard. Pushes event arrays every 2 seconds.

```
event: status
data: {"nodes": [...], "totalObjects": 42, ...}
```

---

### GET /health

Gateway health check.

```json
{ "status": "UP", "service": "vault-gateway", "uptime": 3600 }
```

---

## Repair Jobs

### GET /repairs

List all repair jobs (last 50).

```json
{
  "jobs": [
    {
      "job_id": "...",
      "object_id": "...",
      "target_node_id": "node-3",
      "source_node_id": "node-1",
      "state": "DONE",
      "reason": "MISSING",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

### POST /repairs/trigger

Manually trigger repair scan. Useful for the demo.

```json
{
  "triggered": 2,
  "under_replicated_objects": 2,
  "message": "Triggered 2 repair job(s)"
}
```

---

## Demo / Admin

### POST /admin/corrupt/{nodeId}/{objectId}

Inject corruption into a specific replica (overwrites with random bytes). For hackathon demo only.

```json
{ "injected": true, "node_id": "node-1", "object_id": "..." }
```

---

## Internal (Storage Node → Gateway)

These endpoints are used by storage nodes — not by clients.

### POST /internal/nodes/register

Storage node registration on startup.

### POST /internal/nodes/heartbeat

Periodic heartbeat from storage node.

### POST /internal/corruption

Report corruption detected by integrity scanner.
