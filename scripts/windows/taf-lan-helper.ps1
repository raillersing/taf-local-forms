<#
.SYNOPSIS
    TAf Local Forms - LAN Helper HTTP service.
.DESCRIPTION
    Ecoute sur http://127.0.0.1:8019/ et expose des endpoints allowslist
    pour configurer/tester/desactiver l'acces LAN des eleves.
    Necessite d'etre lance en administrateur pour les actions reseau.
.NOTES
    Auteur: TAf Team
    Necessite: PowerShell 5.1 (Windows), droits admin pour /sync et /disable
#>

param(
    [int]$Port = 8019,
    [string]$BindAddress = "127.0.0.1",
    [int]$DockerPort = 8010,
    [int]$LanPort = 8011
)

$ErrorActionPreference = "Stop"

# --------------------------------------------------
# Helper functions
# --------------------------------------------------
function Get-ActiveLanIp {
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
            Priority       = $prio
            HasGateway     = [bool]$hasGateway
        }
    } | Sort-Object Priority

    $withGateway = $candidates | Where-Object { $_.HasGateway }
    if ($withGateway) { $candidates = $withGateway }
    if ($candidates.Count -ge 1) { return $candidates[0].IPAddress }
    return $null
}

function Get-PortproxyStatus {
    try {
        $output = netsh interface portproxy show all
        $hasRule = $output -match "8011"
        return @{ exists = $hasRule; details = $output }
    } catch {
        return @{ exists = $false; details = ($_.Exception.Message) }
    }
}

function Get-FirewallStatus {
    try {
        $rule = Get-NetFirewallRule -DisplayName "TAf Local Forms - Port 8011" -ErrorAction SilentlyContinue
        if ($rule) {
            return @{ exists = $true; enabled = ($rule.Enabled -eq 'True') }
        }
        return @{ exists = $false; enabled = $false }
    } catch {
        return @{ exists = $false; enabled = $false }
    }
}

function Test-LocalApp {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:$DockerPort/" -Method Head -TimeoutSec 5
        return $true
    } catch {
        return $false
    }
}

function Test-LanUrl {
    param([string]$Ip)
    if (-not $Ip) { return $false }
    try {
        $null = Invoke-WebRequest -Uri "http://$Ip`:$LanPort/" -Method Head -TimeoutSec 5
        return $true
    } catch {
        return $false
    }
}

function Get-Status {
    $lanIp = Get-ActiveLanIp
    $localOk = Test-LocalApp
    $portproxy = Get-PortproxyStatus
    $firewall = Get-FirewallStatus
    $lanOk = if ($lanIp) { Test-LanUrl -Ip $lanIp } else { $false }

    $studentUrl = if ($lanIp) { "http://$lanIp`:$LanPort/" } else { $null }

    return @{
        success     = $true
        lan_ip      = $lanIp
        student_url = $studentUrl
        local_ok    = $localOk
        portproxy   = $portproxy.exists
        firewall    = $firewall.exists
        lan_ok      = $lanOk
        diagnostics = @{
            local_port  = $DockerPort
            lan_port    = $LanPort
            helper_port = $Port
        }
    }
}

function Invoke-Sync {
    $lanIp = Get-ActiveLanIp
    if (-not $lanIp) {
        return @{ success = $false; message = "Aucune adresse LAN detectee." }
    }

    # Portproxy
    try {
        $existing = netsh interface portproxy show all | Select-String "0.0.0.0.*8011"
        if ($existing) {
            netsh interface portproxy delete v4tov4 listenport=$LanPort listenaddress=0.0.0.0 | Out-Null
        }
        netsh interface portproxy add v4tov4 listenport=$LanPort listenaddress=0.0.0.0 connectport=$DockerPort connectaddress=127.0.0.1 | Out-Null
        $proxyOk = $true
    } catch {
        $proxyOk = $false
        $proxyError = $_.Exception.Message
    }

    # Firewall
    try {
        $ruleName = "TAf Local Forms - Port 8011"
        $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        if (-not $existingRule) {
            New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $LanPort -Action Allow | Out-Null
        }
        $fwOk = $true
    } catch {
        $fwOk = $false
        $fwError = $_.Exception.Message
    }

    # WSL sync
    try {
        $syncOutput = wsl -d Ubuntu -e bash -c "cd /home/raillersing/projects/taf-local-forms && docker compose exec -T web python manage.py sync_lan_settings --lan-host $lanIp --lan-port $LanPort" 2>&1
        $wslOk = $true
        $wslMessage = $syncOutput
    } catch {
        $wslOk = $false
        $wslMessage = $_.Exception.Message
    }

    $studentUrl = "http://${lanIp}:${LanPort}/"
    $ok = $proxyOk -and $fwOk

    return @{
        success     = $ok
        message     = if ($ok) { "Acces LAN configure avec succes sur ${lanIp}:${LanPort}." } else { "Erreur lors de la configuration." }
        lan_ip      = $lanIp
        student_url = $studentUrl
        diagnostics = @{
            portproxy = $proxyOk
            firewall  = $fwOk
            wsl_sync  = $wslOk
        }
    }
}

function Invoke-Disable {
    # Remove portproxy
    try {
        $existing = netsh interface portproxy show all | Select-String "0.0.0.0.*8011"
        if ($existing) {
            netsh interface portproxy delete v4tov4 listenport=$LanPort listenaddress=0.0.0.0 | Out-Null
        }
    } catch { }

    # Remove firewall rule
    try {
        $ruleName = "TAf Local Forms - Port 8011"
        $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        if ($existingRule) {
            Remove-NetFirewallRule -DisplayName $ruleName
        }
    } catch { }

    return @{ success = $true; message = "Acces LAN desactive. Portproxy et regle pare-feu supprimes." }
}

function Invoke-Test {
    $lanIp = Get-ActiveLanIp
    $localOk = Test-LocalApp
    $lanOk = if ($lanIp) { Test-LanUrl -Ip $lanIp } else { $false }

    $studentUrl = if ($lanIp) { "http://$lanIp`:$LanPort/" } else { $null }

    return @{
        success     = $true
        message     = if ($lanOk) { "URL eleves accessible : $studentUrl" } else { "URL eleves inaccessible. Verifiez la configuration LAN." }
        lan_ip      = $lanIp
        student_url = $studentUrl
        diagnostics = @{
            local_accessible = $localOk
            lan_accessible   = $lanOk
        }
    }
}

function Invoke-RestartApp {
    try {
        $output = wsl -d Ubuntu -e bash -c "cd /home/raillersing/projects/taf-local-forms && docker compose restart web" 2>&1
        return @{ success = $true; message = "Application redemarree."; output = $output }
    } catch {
        return @{ success = $false; message = "Erreur lors du redemarrage: $($_.Exception.Message)" }
    }
}

function Add-CorsHeaders {
    param($Response, $Origin)
    $allowedOrigins = @("http://localhost:8010", "http://127.0.0.1:8010")
    if ($allowedOrigins -contains $Origin) {
        $Response.Headers.Add("Access-Control-Allow-Origin", $Origin)
        $Response.Headers.Add("Vary", "Origin")
    }
    $Response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    $Response.Headers.Add("Access-Control-Allow-Headers", "Content-Type")
}

function Send-JsonResponse {
    param($Response, $Data)
    $body = ($Data | ConvertTo-Json -Compress)
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($body)
    $Response.ContentType = "application/json"
    $Response.ContentLength64 = $buffer.Length
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
    $Response.OutputStream.Close()
}

function Send-Error {
    param($Response, $Code, $Message)
    $Response.StatusCode = $Code
    Send-JsonResponse $Response @{ success = $false; message = $Message }
}

# --------------------------------------------------
# Server setup
# --------------------------------------------------
$listener = New-Object System.Net.HttpListener
$prefix = "http://${BindAddress}:${Port}/"
$listener.Prefixes.Add($prefix)
$listener.Start()

Write-Host "TAf LAN Helper demarre sur $prefix" -ForegroundColor Green
Write-Host "  Endpoints:" -ForegroundColor Cyan
Write-Host "    GET /status" -ForegroundColor Cyan
Write-Host "    POST /sync" -ForegroundColor Cyan
Write-Host "    POST /restart-app" -ForegroundColor Cyan
Write-Host "    POST /test" -ForegroundColor Cyan
Write-Host "    POST /disable" -ForegroundColor Cyan
Write-Host "  Ecoute uniquement sur 127.0.0.1 (pas accessible depuis le LAN)" -ForegroundColor Yellow
Write-Host ""

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $req = $context.Request
        $res = $context.Response

        $origin = $req.Headers["Origin"]
        $path = $req.Url.AbsolutePath.TrimEnd("/")
        $method = $req.HttpMethod

        # Add CORS headers to every response
        Add-CorsHeaders -Response $res -Origin $origin

        # Handle OPTIONS preflight (always return 204, no action)
        if ($method -eq "OPTIONS") {
            $res.StatusCode = 204
            $res.ContentLength64 = 0
            $res.Close()
            continue
        }

        # Validate Origin header (after OPTIONS which should not be validated)
        $allowedOrigins = @("http://localhost:8010", "http://127.0.0.1:8010", $null, "")
        if ($origin -and ($allowedOrigins -notcontains $origin)) {
            Send-Error $res 403 "Origine non autorisee: $origin"
            $res.Close()
            continue
        }

        try {
            if ($path -eq "/status" -and $method -eq "GET") {
                $data = Get-Status
                Send-JsonResponse $res $data
            } elseif ($path -eq "/sync" -and $method -eq "POST") {
                $data = Invoke-Sync
                Send-JsonResponse $res $data
            } elseif ($path -eq "/restart-app" -and $method -eq "POST") {
                $data = Invoke-RestartApp
                Send-JsonResponse $res $data
            } elseif ($path -eq "/test" -and $method -eq "POST") {
                $data = Invoke-Test
                Send-JsonResponse $res $data
            } elseif ($path -eq "/disable" -and $method -eq "POST") {
                $data = Invoke-Disable
                Send-JsonResponse $res $data
            } elseif ($path -eq "" -or $path -eq "/") {
                Send-JsonResponse $res @{ success = $true; message = "TAf LAN Helper en ecoute." }
            } else {
                Send-Error $res 404 "Endpoint non trouve: $method $path"
            }
        } catch {
            Send-Error $res 500 "Erreur interne: $($_.Exception.Message)"
        }

        $res.Close()
    }
} finally {
    $listener.Stop()
    $listener.Close()
    Write-Host "TAf LAN Helper arrete." -ForegroundColor Yellow
}
