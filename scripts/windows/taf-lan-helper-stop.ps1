<#
.SYNOPSIS
    Arrete le TAf LAN Helper.
.DESCRIPTION
    Trouve et stoppe le processus PowerShell qui execute taf-lan-helper.ps1.
.NOTES
    Auteur: TAf Team
#>

$processes = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -match "taf-lan-helper"
}

if (-not $processes) {
    Write-Host "TAf LAN Helper n'est pas en cours d'execution." -ForegroundColor Yellow
    exit 0
}

foreach ($p in $processes) {
    $p.Kill()
    Write-Host "TAf LAN Helper (PID: $($p.Id)) arrete." -ForegroundColor Green
}
