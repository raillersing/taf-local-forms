#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Installe ou met a jour la tache planifiee "TAf Local Forms LAN Sync".
.DESCRIPTION
    Cree une tache planifiee qui execute taf-lan-sync.ps1 au demarrage
    de session (tout utilisateur) et repete toutes les 5 minutes pendant 1 heure.
.NOTES
    Auteur: TAf Team
    Necessite: PowerShell Administrateur
#>

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TAf Local Forms - Installation de la" -ForegroundColor Cyan
Write-Host "  tache planifiee de synchronisation LAN" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ce script va installer ou mettre a jour une tache planifiee" -ForegroundColor Yellow
Write-Host "qui executera taf-lan-sync.ps1 automatiquement :" -ForegroundColor Yellow
Write-Host "  - Au demarrage de session (tout utilisateur)" -ForegroundColor Yellow
Write-Host "  - Repetition : toutes les 5 minutes pendant 1 heure" -ForegroundColor Yellow
Write-Host "  - Objectif : maintenir le portproxy et le pare-feu a jour" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Voulez-vous continuer? (O/N)"
if ($confirm -ne "O" -and $confirm -ne "o") {
    Write-Host "Operation annulee par l'utilisateur." -ForegroundColor Yellow
    exit 0
}
Write-Host ""

# --------------------------------------------------
# Chemins
# --------------------------------------------------
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$syncScript = Join-Path -Path $scriptDir -ChildPath "taf-lan-sync.ps1"
if (-not (Test-Path -LiteralPath $syncScript)) {
    Write-Host "ERREUR : $syncScript introuvable." -ForegroundColor Red
    exit 1
}

$taskName = "TAf Local Forms LAN Sync"
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$syncScript`""

$trigger = New-ScheduledTaskTrigger -AtLogOn
$trigger.RepetitionInterval = (New-TimeSpan -Minutes 5)
$trigger.RepetitionDuration = (New-TimeSpan -Hours 1)

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# --------------------------------------------------
# Creation ou mise a jour
# --------------------------------------------------
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "La tache '$taskName' existe deja. Mise a jour en cours..." -ForegroundColor Yellow
    Set-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings | Out-Null
    Write-Host "  -> Tache mise a jour avec succes." -ForegroundColor Green
} else {
    Write-Host "Creation de la tache '$taskName'..." -ForegroundColor Yellow
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -User "NT AUTHORITY\SYSTEM" | Out-Null
    Write-Host "  -> Tache creee avec succes." -ForegroundColor Green
}

Write-Host ""
Write-Host "Resume de la tache :" -ForegroundColor Yellow
Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State, Actions, Triggers, Settings
Write-Host ""
Write-Host "Termine." -ForegroundColor Green
