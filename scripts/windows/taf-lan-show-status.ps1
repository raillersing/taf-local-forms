<#
.SYNOPSIS
    Show LAN network status for TAf Local Forms (read-only diagnostic for Windows host).
.DESCRIPTION
    Displays current Windows IP, firewall rule status, portproxy configuration,
    and connectivity test results. Does NOT modify any system setting.
.EXAMPLE
    .\taf-lan-show-status.ps1
.NOTES
    Some checks may require Administrator privileges for complete results.
#>

Write-Host "--- TAf Local Forms: Windows LAN Status ---" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')"
Write-Host ""

# 1. Windows LAN IPs
Write-Host "1. Windows LAN IPs" -ForegroundColor Cyan
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -ne 'WellKnown' } | 
    Select-Object InterfaceAlias, IPAddress, PrefixLength, AddressFamily | Format-Table -AutoSize

# 2. Firewall rules for port 8010
Write-Host "2. Firewall rules on port 8010" -ForegroundColor Cyan
$fwRules = Get-NetFirewallRule -Direction Inbound -Enabled True -ErrorAction SilentlyContinue |
    Where-Object { ($_ | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue).LocalPort -eq 8010 }
if ($fwRules) {
    $fwRules | ForEach-Object {
        $rule = $_
        $portFilter = $_ | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            DisplayName = $rule.DisplayName
            Action = $rule.Action
            Profile = $rule.Profile
            Protocol = $portFilter.Protocol
            LocalPort = $portFilter.LocalPort
        }
    } | Format-Table -AutoSize
} else {
    Write-Host "  No enabled inbound firewall rule found for port 8010." -ForegroundColor Yellow
    Write-Host "  -> Run scripts/windows/taf-lan-open-port.ps1 (as Admin) to create one."
}

# 3. Portproxy config
Write-Host "3. Netsh portproxy" -ForegroundColor Cyan
$pp = netsh interface portproxy show v4tov4 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host $pp
} else {
    Write-Host "  No portproxy configured (not needed when Docker Desktop handles forwarding)." -ForegroundColor Gray
}

# 4. Network profile
Write-Host "4. Network profile" -ForegroundColor Cyan
$profiles = Get-NetConnectionProfile -ErrorAction SilentlyContinue
foreach ($p in $profiles) {
    $isPrivate = if ($p.NetworkCategory -eq 'Private') { 'YES (Private)' } else { "NO ($($p.NetworkCategory))" }
    Write-Host "  $($p.Name): $isPrivate"
}

# 5. Connectivity test
Write-Host "5. Connectivity test (Windows loopback)" -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri 'http://localhost:8010/' -TimeoutSec 5 -UseBasicParsing
    Write-Host "  http://localhost:8010/ -> $($resp.StatusCode) $($resp.StatusDescription)" -ForegroundColor Green
} catch {
    Write-Host "  http://localhost:8010/ -> FAIL ($($_.Exception.Message))" -ForegroundColor Red
}

Write-Host ""
Write-Host "--- End of diagnostic ---" -ForegroundColor Cyan
