#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Configure le portproxy Windows et le pare-feu pour exposer TAf Local Forms sur le LAN.
.DESCRIPTION
    Détecte l'adresse IPv4 active, configure le portproxy (port 8011 -> 8010),
    crée la règle de pare-feu, et tente de synchroniser les paramètres LAN
    via le conteneur Docker Django.
.NOTES
    Auteur: TAf Team
    Nécessite: PowerShell Administrateur, WSL avec Docker
#>

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TAf Local Forms — Synchronisation LAN" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------
# 1. Détection de l'IPv4 active
# --------------------------------------------------
Write-Host "[1/6] Détection de l'adresse IPv4 active..." -ForegroundColor Yellow

$candidates = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.IPAddress -notlike "127.*" -and
    $_.IPAddress -notlike "169.254.*" -and
    $_.InterfaceAlias -notlike "*vEthernet*" -and
    $_.IPAddress -notlike "172.*"
} | ForEach-Object {
    $ip = $_
    $hasGateway = Get-NetRoute -DestinationPrefix "0.0.0.0/0" |
        Where-Object { $_.NextHop -eq $ip.IPAddress }
    $prio = if ($hasGateway) { 0 } else { 1 }
    [PSCustomObject]@{
        IPAddress      = $ip.IPAddress
        InterfaceAlias = $ip.InterfaceAlias
        InterfaceIndex = $ip.InterfaceIndex
        Priority       = $prio
        HasGateway     = [bool]$hasGateway
    }
} | Sort-Object Priority, InterfaceAlias

if (-not $candidates) {
    Write-Host "Aucune interface réseau active trouvée." -ForegroundColor Red
    exit 1
}

# Filtrer : garder celles avec gateway si possible
$withGateway = $candidates | Where-Object { $_.HasGateway }
if ($withGateway) {
    $candidates = $withGateway
}

if ($candidates.Count -eq 1) {
    $selected = $candidates[0]
    Write-Host "  -> Interface détectée : $($selected.InterfaceAlias) — $($selected.IPAddress)" -ForegroundColor Green
} else {
    Write-Host "  Plusieurs interfaces candidates :" -ForegroundColor Yellow
    for ($i = 0; $i -lt $candidates.Count; $i++) {
        Write-Host "  [$i] $($candidates[$i].InterfaceAlias) — $($candidates[$i].IPAddress)"
    }
    $choice = Read-Host "  Choisissez le numéro (défaut: 0)"
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = 0 }
    $selected = $candidates[[int]$choice]
    Write-Host "  -> Sélectionné : $($selected.InterfaceAlias) — $($selected.IPAddress)" -ForegroundColor Green
}

$LanIp = $selected.IPAddress
$LocalDockerPort = 8010
$LanPort = 8011
Write-Host "  -> Adresse LAN : $LanIp`:$LanPort" -ForegroundColor Green
Write-Host ""

# --------------------------------------------------
# 2. Vérification locale de Docker
# --------------------------------------------------
Write-Host "[2/6] Vérification de http://localhost:$LocalDockerPort/..." -ForegroundColor Yellow
try {
    $null = Invoke-WebRequest -Uri "http://localhost:$LocalDockerPort/" -Method Head -TimeoutSec 5
    Write-Host "  -> OK : le service est accessible." -ForegroundColor Green
} catch {
    Write-Host "  -> ÉCHEC : http://localhost:$LocalDockerPort/ est inaccessible." -ForegroundColor Red
    Write-Host "     Assurez-vous que le conteneur Docker tourne." -ForegroundColor Red
    exit 1
}
Write-Host ""

# --------------------------------------------------
# 3. Configuration du portproxy
# --------------------------------------------------
Write-Host "[3/6] Configuration du portproxy Windows..." -ForegroundColor Yellow

# Supprimer l'ancienne entrée pour 0.0.0.0:8011
$existing = netsh interface portproxy show all | Select-String "0.0.0.0.*8011"
if ($existing) {
    netsh interface portproxy delete v4tov4 listenport=$LanPort listenaddress=0.0.0.0 | Out-Null
    Write-Host "  -> Ancienne règle supprimée." -ForegroundColor Yellow
}

netsh interface portproxy add v4tov4 listenport=$LanPort listenaddress=0.0.0.0 connectport=$LocalDockerPort connectaddress=127.0.0.1 | Out-Null
Write-Host "  -> Portproxy ajouté : 0.0.0.0:$LanPort -> 127.0.0.1:$LocalDockerPort" -ForegroundColor Green
Write-Host ""

# --------------------------------------------------
# 4. Configuration du pare-feu
# --------------------------------------------------
Write-Host "[4/6] Configuration du pare-feu Windows..." -ForegroundColor Yellow

$ruleName = "TAf Local Forms - Port 8011"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existingRule) {
    Write-Host "  -> La règle de pare-feu existe déjà." -ForegroundColor Yellow
} else {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $LanPort -Action Allow | Out-Null
    Write-Host "  -> Règle de pare-feu créée : $ruleName" -ForegroundColor Green
}
Write-Host ""

# --------------------------------------------------
# 5. Synchronisation Django (WSL)
# --------------------------------------------------
Write-Host "[5/6] Synchronisation des paramètres LAN Django..." -ForegroundColor Yellow

$wslCmd = "cd /home/raillersing/projects/taf-local-forms && docker compose exec -T web python manage.py sync_lan_settings --lan-host $LanIp --lan-port $LanPort 2>&1"
try {
    $output = wsl -e sh -c $wslCmd 2>&1
    Write-Host "  -> Succès :" -ForegroundColor Green
    $output | ForEach-Object { Write-Host "     $_" }
} catch {
    Write-Host "  -> Impossible d'exécuter la commande dans WSL." -ForegroundColor Red
    Write-Host "     Démarre d'abord docker compose up -d depuis WSL puis relance ce script." -ForegroundColor Red
}
Write-Host ""

# --------------------------------------------------
# 6. Affichage des URLs
# --------------------------------------------------
Write-Host "[6/6] URLs finales" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Formateur : http://localhost:$LocalDockerPort/" -ForegroundColor Green
Write-Host "  Élèves    : http://$LanIp`:$LanPort/" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Modules disponibles :" -ForegroundColor Yellow
Write-Host "  - Questionnaire : http://$LanIp`:$LanPort/questionnaire/" -ForegroundColor Cyan
Write-Host "  - Évaluation   : http://$LanIp`:$LanPort/evaluation/" -ForegroundColor Cyan
Write-Host "  - Administration : http://$LanIp`:$LanPort/admin/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminé." -ForegroundColor Green
