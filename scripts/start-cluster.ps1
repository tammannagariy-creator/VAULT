#!/usr/bin/env pwsh
# scripts/start-cluster.ps1
#
# Start Vault cluster locally (without Docker) for development.
# Runs: 1 gateway + 3 storage nodes as separate processes.
#
# Usage: .\scripts\start-cluster.ps1
# Stop:  Ctrl+C (stops all child processes)

param(
    [int]$ReplicationFactor = 3,
    [int]$WriteQuorum = 2,
    [int]$ReadQuorum = 2,
    [int]$HeartbeatTimeout = 15000,
    [int]$RepairInterval = 10000
)

$VaultRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          VAULT — STARTING CLUSTER            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Replication Factor : N=$ReplicationFactor"
Write-Host "  Write Quorum       : W=$WriteQuorum"
Write-Host "  Read Quorum        : R=$ReadQuorum"
Write-Host ""

# Create data directories
New-Item -ItemType Directory -Path "$VaultRoot\data\gateway" -Force | Out-Null
New-Item -ItemType Directory -Path "$VaultRoot\data\node-1" -Force | Out-Null
New-Item -ItemType Directory -Path "$VaultRoot\data\node-2" -Force | Out-Null
New-Item -ItemType Directory -Path "$VaultRoot\data\node-3" -Force | Out-Null

$jobs = @()

# Start Gateway
Write-Host "Starting gateway on port 8080..." -ForegroundColor Green
$gatewayEnv = @{
    GATEWAY_PORT         = "8080"
    REPLICATION_FACTOR   = "$ReplicationFactor"
    WRITE_QUORUM         = "$WriteQuorum"
    READ_QUORUM          = "$ReadQuorum"
    HEARTBEAT_INTERVAL   = "5000"
    HEARTBEAT_TIMEOUT    = "$HeartbeatTimeout"
    REPAIR_INTERVAL      = "$RepairInterval"
    SCAN_INTERVAL        = "60000"
    METADATA_DATABASE    = "$VaultRoot\data\gateway\vault.db"
}

$gatewayJob = Start-Job -ScriptBlock {
    param($root, $env)
    Set-Location $root
    foreach ($key in $env.Keys) { [Environment]::SetEnvironmentVariable($key, $env[$key]) }
    npx tsx src/gateway/index.ts 2>&1
} -ArgumentList $VaultRoot, $gatewayEnv

$jobs += $gatewayJob
Write-Host "  Gateway started (job $($gatewayJob.Id))" -ForegroundColor Green

# Wait for gateway to be ready
Write-Host "Waiting for gateway to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 2 -ErrorAction Stop
        if ($resp.status -eq "UP") { $ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 1
}

if (-not $ready) {
    Write-Host "Gateway failed to start!" -ForegroundColor Red
    $jobs | Stop-Job
    exit 1
}
Write-Host "  Gateway is ready!" -ForegroundColor Green

# Start Storage Nodes
$nodeConfigs = @(
    @{ Id = "node-1"; Port = 8081 },
    @{ Id = "node-2"; Port = 8082 },
    @{ Id = "node-3"; Port = 8083 }
)

foreach ($node in $nodeConfigs) {
    Write-Host "Starting $($node.Id) on port $($node.Port)..." -ForegroundColor Green
    $nodeEnv = @{
        NODE_ID              = $node.Id
        NODE_PORT            = "$($node.Port)"
        NODE_ADDRESS         = "localhost"
        STORAGE_PATH         = "$VaultRoot\data\$($node.Id)"
        GATEWAY_ADDRESS      = "localhost"
        GATEWAY_PORT         = "8080"
        HEARTBEAT_INTERVAL   = "5000"
        HEARTBEAT_TIMEOUT    = "$HeartbeatTimeout"
        SCAN_INTERVAL        = "60000"
    }

    $nodeJob = Start-Job -ScriptBlock {
        param($root, $env)
        Set-Location $root
        foreach ($key in $env.Keys) { [Environment]::SetEnvironmentVariable($key, $env[$key]) }
        npx tsx src/storage/index.ts 2>&1
    } -ArgumentList $VaultRoot, $nodeEnv

    $jobs += $nodeJob
    Write-Host "  $($node.Id) started (job $($nodeJob.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           VAULT CLUSTER IS RUNNING           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Gateway API  : http://localhost:8080"
Write-Host "  Node 1       : http://localhost:8081"
Write-Host "  Node 2       : http://localhost:8082"
Write-Host "  Node 3       : http://localhost:8083"
Write-Host "  Cluster Status: http://localhost:8080/cluster/status"
Write-Host "  Event Stream : http://localhost:8080/cluster/events/stream"
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Stream logs from all jobs
try {
    while ($true) {
        foreach ($job in $jobs) {
            $output = Receive-Job -Job $job
            if ($output) {
                Write-Host $output
            }
        }
        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    $jobs | Stop-Job
    $jobs | Remove-Job
    Write-Host "Stopped." -ForegroundColor Green
}
