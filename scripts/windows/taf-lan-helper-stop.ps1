<#
.SYNOPSIS
    Arrete le TAf LAN Helper.
.DESCRIPTION
    Stoppe le processus PowerShell du helper en utilisant le PID file
    ou en cherchant le processus par CommandLine. Verifie que le port
    8019 est libere.
.NOTES
    Auteur: TAf Team
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logDir = Join-Path $projectRoot "logs\windows"
$pidFile = Join-Path $logDir "taf-lan-helper.pid"
$helperUrl = "http://127.0.0.1:8019/"
$helperPort = 8019

$stopped = $false

# Step 1: Try PID file
if (Test-Path $pidFile) {
    try {
        $pid = Get-Content $pidFile -Raw | ForEach-Object { $_.Trim() }
        if ($pid -match '^\d+$') {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "Helper trouve via PID file (PID: $pid). Arret..." -ForegroundColor Cyan
                $proc.Kill()
                Write-Host "  Processus tue." -ForegroundColor Green
                $stopped = $true
            } else {
                Write-Host "PID file present mais processus $pid introuvable." -ForegroundColor Yellow
            }
        }
        Remove-Item $pidFile -Force
    } catch {
        Write-Host "Erreur lecture PID file: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Step 2: Fallback — find by CommandLine
if (-not $stopped) {
    $processes = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "taf-lan-helper"
    }
    if ($processes) {
        foreach ($p in $processes) {
            Write-Host "Helper trouve via CommandLine (PID: $($p.Id)). Arret..." -ForegroundColor Cyan
            $p.Kill()
            Write-Host "  Processus tue." -ForegroundColor Green
            $stopped = $true
        }
    } else {
        Write-Host "TAf LAN Helper n'est pas en cours d'execution." -ForegroundColor Yellow
        exit 0
    }
}

# Step 3: Wait for port to be freed
Start-Sleep -Seconds 1
try {
    $conn = Get-NetTCPConnection -LocalPort $helperPort -ErrorAction SilentlyContinue
    if (-not $conn) {
        Write-Host "Port $helperPort libere." -ForegroundColor Green
    } else {
        Write-Host "Attention: port $helperPort toujours en ecoute (OwningProcess: $($conn.OwningProcess))." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Port $helperPort libere." -ForegroundColor Green
}

Write-Host "TAf LAN Helper arrete." -ForegroundColor Green
exit 0
