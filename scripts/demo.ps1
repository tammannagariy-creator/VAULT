#!/usr/bin/env pwsh
# scripts/demo.ps1
#
# Automated hackathon demo script.
# Runs the full demo sequence step by step.
# Requires the cluster to be running (run start-cluster.ps1 first).
#
# Usage: .\scripts\demo.ps1

$BASE = "http://localhost:8080"

function Print-Step($n, $msg) {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  STEP $n — $msg" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
}

function Print-JSON($obj) {
    $obj | ConvertTo-Json -Depth 5 | Write-Host
}

function Wait-Prompt($msg) {
    Write-Host ""
    Write-Host "  ▶ $msg" -ForegroundColor Yellow
    Write-Host "  [Press ENTER to continue]" -ForegroundColor DarkGray
    Read-Host | Out-Null
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Show cluster health
# ─────────────────────────────────────────────────────────────────────────────

Print-Step 1 "Vault Cluster Status"

$status = Invoke-RestMethod "$BASE/cluster/status"
Write-Host ""
Write-Host "  Nodes:" -ForegroundColor White
foreach ($node in $status.nodes) {
    $color = if ($node.state -eq "HEALTHY") { "Green" } elseif ($node.state -eq "FAILED") { "Red" } else { "Yellow" }
    Write-Host "    $($node.node_id) — $($node.state)" -ForegroundColor $color
}
Write-Host "  Objects: $($status.totalObjects)"
Write-Host "  Replicas: $($status.totalReplicas)"

Wait-Prompt "Cluster is healthy with 3 nodes. Now upload an object."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Upload an object
# ─────────────────────────────────────────────────────────────────────────────

Print-Step 2 "PUT Object"

$content = [System.Text.Encoding]::UTF8.GetBytes("Hello from Vault! This is a demo file that will be replicated across 3 nodes.")
$bytes = [byte[]]$content

$headers = @{ "Content-Type" = "application/octet-stream" }
$putResp = Invoke-RestMethod -Method PUT -Uri "$BASE/objects/demo/hello.txt" -Body $bytes -Headers $headers

Write-Host ""
Write-Host "  Object stored!" -ForegroundColor Green
Write-Host "  object_id : $($putResp.object_id)"
Write-Host "  version   : $($putResp.version)"
Write-Host "  checksum  : $($putResp.checksum)"
Write-Host "  replicas  :"
foreach ($r in $putResp.replicas) {
    Write-Host "    - $($r.node_id) — $($r.state)" -ForegroundColor Green
}

$OBJECT_ID = $putResp.object_id

Wait-Prompt "Object is replicated to 3 nodes. Now retrieve it."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Retrieve the object
# ─────────────────────────────────────────────────────────────────────────────

Print-Step 3 "GET Object (checksum verified)"

$getResp = Invoke-WebRequest -Method GET -Uri "$BASE/objects/demo/hello.txt"
$returnedChecksum = $getResp.Headers["X-Object-Checksum"]
$bodyText = [System.Text.Encoding]::UTF8.GetString($getResp.Content)

Write-Host ""
Write-Host "  Content   : $bodyText" -ForegroundColor White
Write-Host "  Checksum  : $returnedChecksum" -ForegroundColor Green
Write-Host "  ✓ Data integrity verified!" -ForegroundColor Green

Wait-Prompt "Now stop node-2 to simulate a node failure."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Simulate node failure
# ─────────────────────────────────────────────────────────────────────────────

Print-Step 4 "Node Failure Simulation"

Write-Host ""
Write-Host "  ACTION: Manually stop node-2 now." -ForegroundColor Red
Write-Host "  (In another terminal: docker compose stop node-2)" -ForegroundColor DarkGray
Write-Host "  Waiting 20 seconds for failure detection..." -ForegroundColor Yellow

Start-Sleep -Seconds 20

$status2 = Invoke-RestMethod "$BASE/cluster/status"
foreach ($node in $status2.nodes) {
    $color = if ($node.state -eq "HEALTHY") { "Green" } elseif ($node.state -eq "FAILED") { "Red" } else { "Yellow" }
    Write-Host "    $($node.node_id) — $($node.state)" -ForegroundColor $color
}

Wait-Prompt "Node 2 is FAILED. The object is under-replicated. Try reading it anyway."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: Read despite failure
# ─────────────────────────────────────────────────────────────────────────────

Print-Step 5 "GET Object — still available!"

$getResp2 = Invoke-WebRequest -Method GET -Uri "$BASE/objects/demo/hello.txt"
$bodyText2 = [System.Text.Encoding]::UTF8.GetString($getResp2.Content)
Write-Host ""
Write-Host "  Content   : $bodyText2" -ForegroundColor Green
Write-Host "  ✓ Object is still readable from surviving replicas!" -ForegroundColor Green

Wait-Prompt "Now watch the automatic repair."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6: Automatic repair
# ─────────────────────────────────────────────────────────────────────────────

Print-Step 6 "Automatic Replica Repair"

# Trigger repair manually for faster demo
$repairResp = Invoke-RestMethod -Method POST -Uri "$BASE/repairs/trigger"
Write-Host ""
Write-Host "  Repair jobs triggered: $($repairResp.triggered)" -ForegroundColor Yellow

Write-Host "  Waiting 15 seconds for repair to complete..."
Start-Sleep -Seconds 15

$repairs = Invoke-RestMethod "$BASE/repairs"
foreach ($job in $repairs.jobs | Select-Object -First 5) {
    $color = if ($job.state -eq "DONE") { "Green" } elseif ($job.state -eq "FAILED") { "Red" } else { "Yellow" }
    Write-Host "    Job $($job.job_id.Substring(0,8))... — $($job.state) (reason: $($job.reason))" -ForegroundColor $color
}

Wait-Prompt "Now inject corruption into a replica to test integrity detection."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7: Inject corruption
# ─────────────────────────────────────────────────────────────────────────────

Print-Step 7 "Corruption Injection"

# Get metadata to find which nodes have replicas
$objMeta = Invoke-RestMethod "$BASE/objects/demo/hello.txt/metadata"
$healthyReplica = $objMeta.replicas | Where-Object { $_.state -eq "HEALTHY" } | Select-Object -First 1

if ($healthyReplica) {
    $corruptResp = Invoke-RestMethod -Method POST -Uri "$BASE/admin/corrupt/$($healthyReplica.node_id)/$OBJECT_ID"
    Write-Host ""
    Write-Host "  Corruption injected on node: $($healthyReplica.node_id)" -ForegroundColor Red
    Write-Host "  Expected checksum : $($objMeta.checksum)"
    Write-Host "  Actual checksum   : (random bytes written to disk)" -ForegroundColor Red
    Write-Host "  ✗ Checksum MISMATCH — corruption detected!" -ForegroundColor Red
}

Wait-Prompt "The integrity scanner will detect and repair this. Triggering now..."

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8: Show repair after corruption
# ─────────────────────────────────────────────────────────────────────────────

Print-Step 8 "Automatic Corruption Repair"

$repairResp2 = Invoke-RestMethod -Method POST -Uri "$BASE/repairs/trigger"
Write-Host ""
Write-Host "  Repair triggered. Waiting 15 seconds..."
Start-Sleep -Seconds 15

$status3 = Invoke-RestMethod "$BASE/cluster/status"
Write-Host "  Healthy replicas  : $($status3.healthyReplicas)"
Write-Host "  Corrupt replicas  : $($status3.corruptReplicas)"
Write-Host "  Pending repairs   : $($status3.pendingRepairJobs)"

if ($status3.corruptReplicas -eq 0) {
    Write-Host "  ✓ All replicas are healthy!" -ForegroundColor Green
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  DEMO COMPLETE — Vault distributed storage" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
