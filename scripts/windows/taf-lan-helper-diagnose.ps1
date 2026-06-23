<#
.SYNOPSIS
    Diagnostique l'etat du TAf LAN Helper.
.DESCRIPTION
    Affiche le statut du processus helper, du port 8019, teste /status,
    et affiche les dernieres lignes du log.
.NOTES
    Auteur: TAf Team
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logDir = Join-Path $projectRoot "logs\windows"
$pidFile = Join-Path $logDir "taf-lan-helper.pid"
$logFile = Join-Path $logDir "taf-lan-helper.log"
$helperUrl = "http://127.0.0.1:8019/status"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TAf LAN Helper — Diagnostic" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. PID file
Write-Host "--- PID file ---" -ForegroundColor Yellow
if (Test-Path $pidFile) {
    $pid = Get-Content $pidFile -Raw | ForEach-Object { $_.Trim() }
    Write-Host "  Fichier: $pidFile" -ForegroundColor Green
    Write-Host "  PID: $pid" -ForegroundColor Green
} else {
    Write-Host "  Aucun PID file." -ForegroundColor Yellow
}

# 2. Process helper
Write-Host ""
Write-Host "--- Processus helper ---" -ForegroundColor Yellow
$processes = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -match "taf-lan-helper"
}
if ($processes) {
    foreach ($p in $processes) {
        Write-Host "  PID: $($p.Id)" -ForegroundColor Green
        Write-Host "  CPU: $($p.CPU)s" -ForegroundColor Green
        Write-Host "  Memoire: $([math]::Round($p.WorkingSet64 / 1MB, 1)) MB" -ForegroundColor Green
        Write-Host "  Lance: $($p.StartTime)" -ForegroundColor Green
    }
} else {
    Write-Host "  Aucun processus helper trouve." -ForegroundColor Yellow
}

# 3. Port 8019
Write-Host ""
Write-Host "--- Port 8019 ---" -ForegroundColor Yellow
try {
    $conn = Get-NetTCPConnection -LocalPort 8019 -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "  Etat: $($conn.State)" -ForegroundColor Green
        Write-Host "  OwningProcess: $($conn.OwningProcess)" -ForegroundColor Green
    } else {
        Write-Host "  Port 8019 non ecoute." -ForegroundColor Red
    }
} catch {
    Write-Host "  Port 8019 non ecoute." -ForegroundColor Red
}

# 4. Test /status
Write-Host ""
Write-Host "--- Test /status ---" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $helperUrl -Method GET -TimeoutSec 3 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "  Statut: HTTP $($response.StatusCode) OK" -ForegroundColor Green
        $data = $response.Content | ConvertFrom-Json
        Write-Host "  Message: $($data.message)" -ForegroundColor Green
        Write-Host "  Version: $($data.version)" -ForegroundColor Green
        Write-Host "  PID helper: $($data.helper_pid)" -ForegroundColor Green
        Write-Host "  Timestamp: $($data.timestamp)" -ForegroundColor Green
        if ($data.lan_ip) {
            Write-Host "  IP LAN: $($data.lan_ip)" -ForegroundColor Green
        } else {
            Write-Host "  IP LAN: non detectee" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Statut: HTTP $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "  /status inaccessible: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Log
Write-Host ""
Write-Host "--- Log (10 dernieres lignes) ---" -ForegroundColor Yellow
if (Test-Path $logFile) {
    Write-Host "  Fichier: $logFile" -ForegroundColor Cyan
    $logLines = Get-Content $logFile -Tail 10
    foreach ($line in $logLines) {
        if ($line -match "ERROR") {
            Write-Host "  $line" -ForegroundColor Red
        } elseif ($line -match "WARN") {
            Write-Host "  $line" -ForegroundColor Yellow
        } else {
            Write-Host "  $line" -ForegroundColor White
        }
    }
} else {
    Write-Host "  Aucun fichier log trouve." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnostic termine." -ForegroundColor Cyan
