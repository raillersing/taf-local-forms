<#
.SYNOPSIS
    Demarre le TAf LAN Helper en arriere-plan.
.DESCRIPTION
    Lance taf-lan-helper.ps1 dans une fenetre PowerShell cachee.
    Necessite: droits administrateur.
.NOTES
    Auteur: TAf Team
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$helperPath = Join-Path $scriptDir "taf-lan-helper.ps1"

if (-not (Test-Path $helperPath)) {
    Write-Host "ERREUR: $helperPath introuvable." -ForegroundColor Red
    exit 1
}

$existing = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -match "taf-lan-helper"
}
if ($existing) {
    Write-Host "TAf LAN Helper est deja en cours d'execution (PID: $($existing.Id))." -ForegroundColor Yellow
    exit 0
}

$startArgs = "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$helperPath`""
Start-Process -FilePath "powershell.exe" -ArgumentList $startArgs -Verb RunAs

Write-Host "TAf LAN Helper demarre en arriere-plan." -ForegroundColor Green
Write-Host "URL: http://127.0.0.1:8019/" -ForegroundColor Cyan
