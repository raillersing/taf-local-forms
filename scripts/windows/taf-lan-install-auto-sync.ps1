#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Installe ou met à jour la tâche planifiée « TAf Local Forms LAN Sync ».
.DESCRIPTION
    Crée une tâche planifiée qui exécute taf-lan-sync.ps1 au démarrage
    de session (tout utilisateur) et répète toutes les 5 minutes pendant 1 heure.
.NOTES
    Auteur: TAf Team
    Nécessite: PowerShell Administrateur
#>

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TAf Local Forms — Installation de la" -ForegroundColor Cyan
Write-Host "  tâche planifiée de synchronisation LAN" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ce script va installer ou mettre à jour une tâche planifiée" -ForegroundColor Yellow
Write-Host "qui exécutera taf-lan-sync.ps1 automatiquement :" -ForegroundColor Yellow
Write-Host "  - Au démarrage de session (tout utilisateur)" -ForegroundColor Yellow
Write-Host "  - Répétition : toutes les 5 minutes pendant 1 heure" -ForegroundColor Yellow
Write-Host "  - Objectif : maintenir le portproxy et le pare-feu à jour" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Voulez-vous continuer? (O/N)"
if ($confirm -ne "O" -and $confirm -ne "o") {
    Write-Host "Opération annulée par l'utilisateur." -ForegroundColor Yellow
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
# Création ou mise à jour
# --------------------------------------------------
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "La tâche '$taskName' existe déjà. Mise à jour en cours..." -ForegroundColor Yellow
    Set-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings | Out-Null
    Write-Host "  -> Tâche mise à jour avec succès." -ForegroundColor Green
} else {
    Write-Host "Création de la tâche '$taskName'..." -ForegroundColor Yellow
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -User "NT AUTHORITY\SYSTEM" | Out-Null
    Write-Host "  -> Tâche créée avec succès." -ForegroundColor Green
}

Write-Host ""
Write-Host "Résumé de la tâche :" -ForegroundColor Yellow
Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State, Actions, Triggers, Settings
Write-Host ""
Write-Host "Terminé." -ForegroundColor Green
