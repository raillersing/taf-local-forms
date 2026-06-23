<#
.SYNOPSIS
    Demarre le TAf LAN Helper en arriere-plan.
.DESCRIPTION
    Lance taf-lan-helper.ps1 en arriere-plan avec droits administrateur,
    attend que /status reponde HTTP 200, et confirme le demarrage.
    Necessite: droits administrateur.
.NOTES
    Auteur: TAf Team
#>

$ErrorActionPreference = "Stop"

# Paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$helperPath = Join-Path $scriptDir "taf-lan-helper.ps1"
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logDir = Join-Path $projectRoot "logs\windows"
$pidFile = Join-Path $logDir "taf-lan-helper.pid"
$helperUrl = "http://127.0.0.1:8019/status"

if (-not (Test-Path $helperPath)) {
    Write-Host "ERREUR: Fichier helper introuvable: $helperPath" -ForegroundColor Red
    exit 1
}

# Check if already running via /status
try {
    $existingResponse = Invoke-WebRequest -Uri $helperUrl -Method GET -TimeoutSec 2 -ErrorAction Stop
    if ($existingResponse.StatusCode -eq 200) {
        Write-Host "TAf LAN Helper est deja en cours d'execution." -ForegroundColor Yellow
        try {
            $data = $existingResponse.Content | ConvertFrom-Json
            Write-Host "  PID: $($data.helper_pid)" -ForegroundColor Cyan
            Write-Host "  Version: $($data.version)" -ForegroundColor Cyan
        } catch {}
        exit 0
    }
} catch {
    # Helper not responding, that's fine — will start it
}

# Start helper in background (elevated)
Write-Host "Demarrage du TAf LAN Helper..." -ForegroundColor Cyan
$startArgs = "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$helperPath`""
$proc = Start-Process -FilePath "powershell.exe" -ArgumentList $startArgs -Verb RunAs -PassThru -WindowStyle Hidden

if (-not $proc) {
    Write-Host "ERREUR: Impossible de lancer le processus helper." -ForegroundColor Red
    exit 1
}

Write-Host "  Processus lance (PID: $($proc.Id)). Verification du statut..." -ForegroundColor Cyan

# Wait for helper to become responsive (poll /status)
$maxAttempts = 10
$attempt = 0
$started = $false

while ($attempt -lt $maxAttempts) {
    Start-Sleep -Milliseconds 500
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri $helperUrl -Method GET -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $started = $true
            break
        }
    } catch {
        # Not ready yet, keep waiting
    }
}

if ($started) {
    Write-Host "TAf LAN Helper demarre avec succes." -ForegroundColor Green
    Write-Host "  URL: http://127.0.0.1:8019/" -ForegroundColor Cyan
    Write-Host "  PID: $($proc.Id)" -ForegroundColor Cyan
    Write-Host "  Log: $logDir\taf-lan-helper.log" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "ERREUR: Le helper n'a pas rependu apres $($maxAttempts * 0.5) secondes." -ForegroundColor Red
    Write-Host "  Log: $logDir\taf-lan-helper.log" -ForegroundColor Yellow
    Write-Host "  PID: $($proc.Id)" -ForegroundColor Yellow
    Write-Host "Arret du processus..." -ForegroundColor Yellow
    try { $proc.Kill() } catch {}
    try {
        if (Test-Path $pidFile) { Remove-Item $pidFile -Force }
    } catch {}
    exit 1
}
