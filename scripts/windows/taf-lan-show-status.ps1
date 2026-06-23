<#
.SYNOPSIS
    Affiche l'etat actuel de la configuration LAN pour TAf Local Forms.
.DESCRIPTION
    Script read-only qui inspecte l'interface reseau active, le portproxy,
    la regle de pare-feu, et teste la connectivite locale et LAN.
.NOTES
    Auteur: TAf Team
#>

$ErrorActionPreference = "Continue"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TAf Local Forms - Etat de la configuration LAN" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------
# 1. Detection de l'IPv4 active
# --------------------------------------------------
Write-Host "[1] Interface reseau active" -ForegroundColor Yellow

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

$withGateway = $candidates | Where-Object { $_.HasGateway }
if ($withGateway) {
    $candidates = $withGateway
}

$LanIp = $null
if ($candidates.Count -ge 1) {
    $selected = $candidates[0]
    $LanIp = $selected.IPAddress
    Write-Host "  Interface : $($selected.InterfaceAlias)" -ForegroundColor Green
    Write-Host "  Adresse   : $LanIp" -ForegroundColor Green
    Write-Host "  Passerelle: $(if ($selected.HasGateway) { 'Oui' } else { 'Non' })" -ForegroundColor Green
} else {
    Write-Host "  Aucune interface active trouvee." -ForegroundColor Red
}
Write-Host ""

# --------------------------------------------------
# 2. Portproxy
# --------------------------------------------------
Write-Host "[2] Portproxy Windows" -ForegroundColor Yellow
$portproxy = netsh interface portproxy show all
if ($portproxy -match "8011") {
    Write-Host "  Regle 8011 trouvee :" -ForegroundColor Green
    $portproxy | ForEach-Object { Write-Host "     $_" }
} else {
    Write-Host "  Aucune regle portproxy pour le port 8011." -ForegroundColor Red
}
Write-Host ""

# --------------------------------------------------
# 3. Pare-feu
# --------------------------------------------------
Write-Host "[3] Pare-feu - Regle 'TAf Local Forms - Port 8011'" -ForegroundColor Yellow
$rule = Get-NetFirewallRule -DisplayName "TAf Local Forms - Port 8011" -ErrorAction SilentlyContinue
if ($rule) {
    Write-Host "  Statut : $(if ($rule.Enabled -eq 'True') { 'Activee' } else { 'Desactivee' })" -ForegroundColor Green
    $rule | Format-List DisplayName, Direction, Enabled, Action, Profile
    $portFilter = $rule | Get-NetFirewallPortFilter
    if ($portFilter) {
        Write-Host "  Port : $($portFilter.LocalPort)" -ForegroundColor Cyan
        Write-Host "  Protocole : $($portFilter.Protocol)" -ForegroundColor Cyan
    }
} else {
    Write-Host "  La regle n'existe pas." -ForegroundColor Red
}
Write-Host ""

# --------------------------------------------------
# 4. Test localhost:8010
# --------------------------------------------------
Write-Host "[4] Test http://localhost:8010/" -ForegroundColor Yellow
try {
    $null = Invoke-WebRequest -Uri "http://localhost:8010/" -Method Head -TimeoutSec 5
    Write-Host "  -> Accessible" -ForegroundColor Green
} catch {
    Write-Host "  -> Inaccessible" -ForegroundColor Red
}
Write-Host ""

# --------------------------------------------------
# 5. Test LAN IP
# --------------------------------------------------
Write-Host "[5] Test http://$LanIp`:8011/" -ForegroundColor Yellow
if ($LanIp) {
    try {
        $null = Invoke-WebRequest -Uri "http://$LanIp`:8011/" -Method Head -TimeoutSec 5
        Write-Host "  -> Accessible depuis le LAN" -ForegroundColor Green
    } catch {
        Write-Host "  -> Inaccessible (le portproxy ou le pare-feu peut ne pas etre configure)" -ForegroundColor Red
    }
} else {
    Write-Host "  -> Impossible (pas d'adresse LAN detectee)" -ForegroundColor Red
}
Write-Host ""

# --------------------------------------------------
# 6. URL eleve
# --------------------------------------------------
Write-Host "[6] URL pour les eleves" -ForegroundColor Yellow
if ($LanIp) {
    Write-Host "  http://$LanIp`:8011/" -ForegroundColor Green
    Write-Host "  http://$LanIp`:8011/module-2/" -ForegroundColor Cyan
    Write-Host "  http://$LanIp`:8011/module-3/" -ForegroundColor Cyan
    Write-Host "  http://$LanIp`:8011/module-4/" -ForegroundColor Cyan
    Write-Host "  http://$LanIp`:8011/module-5/" -ForegroundColor Cyan
    Write-Host "  http://$LanIp`:8011/module-6/" -ForegroundColor Cyan
    Write-Host "  http://$LanIp`:8011/module-7/" -ForegroundColor Cyan
} else {
    Write-Host "  Non disponible (pas d'adresse LAN)." -ForegroundColor Red
}
Write-Host ""
Write-Host "Termine." -ForegroundColor Green
