<#
.SYNOPSIS
    Create Windows Firewall rule to allow inbound access to TAf Local Forms on port 8010.
.DESCRIPTION
    This script creates (or updates) a Windows Firewall inbound rule named "TAf Local Forms - Port 8010"
    to allow TCP connections on port 8010. Run as Administrator.
.EXAMPLE
    .\taf-lan-open-port.ps1
.NOTES
    Administrator privileges required. This script is READ-ONLY safe: it only modifies
    the Windows Firewall. It does NOT modify any application configuration.
#>

$ruleName = "TAf Local Forms - Port 8010"
$port = 8010

Write-Host "--- TAf Local Forms: Windows Firewall Rule ---" -ForegroundColor Cyan
Write-Host "Rule name: $ruleName"
Write-Host "Port:      $port (TCP inbound)"
Write-Host ""

# Check if rule already exists
$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Rule already exists. Current state:" -ForegroundColor Yellow
    $existing | Format-Table DisplayName, Direction, Action, Enabled, Profile -AutoSize
    $choice = Read-Host "Delete and recreate? (y/N)"
    if ($choice -eq 'y') {
        Remove-NetFirewallRule -DisplayName $ruleName
        Write-Host "Old rule removed." -ForegroundColor Green
    } else {
        Write-Host "Keeping existing rule." -ForegroundColor Green
        exit 0
    }
}

# Create rule
try {
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $port `
        -Action Allow `
        -Profile Any `
        -Description "Permet l'acces LAN à TAf Local Forms sur le port $port"
    Write-Host "Firewall rule created successfully." -ForegroundColor Green
} catch {
    Write-Host "ERROR: Could not create firewall rule: $_" -ForegroundColor Red
    exit 1
}

# Verify
$newRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($newRule) {
    Write-Host "Rule verified:" -ForegroundColor Green
    $newRule | Format-Table DisplayName, Direction, Action, Enabled, Profile -AutoSize
} else {
    Write-Host "WARNING: Rule created but not found on verification." -ForegroundColor Yellow
}
