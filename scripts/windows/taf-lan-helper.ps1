<#
.SYNOPSIS
    TAf Local Forms - LAN Helper HTTP service.
.DESCRIPTION
    Ecoute sur http://127.0.0.1:8019/ et expose des endpoints allowslist
    pour configurer/tester/desactiver l'acces LAN des eleves.
    Necessite d'etre lance en administrateur pour les actions reseau.
    Ecrit des logs dans logs/windows/taf-lan-helper.log.
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
# Log / PID setup
# --------------------------------------------------
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logDir = Join-Path $projectRoot "logs\windows"
if (-not (Test-Path $logDir)) {
    $null = New-Item -ItemType Directory -Path $logDir -Force
}
$logFile = Join-Path $logDir "taf-lan-helper.log"
$pidFile = Join-Path $logDir "taf-lan-helper.pid"
$helperVersion = "1.1.0"

function Write-Log {
    param($Level, $Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] [$Level] $Message"
    try {
        Add-Content -Path $logFile -Value $line -ErrorAction SilentlyContinue
    } catch {}
    Write-Host $line
}

# Write PID file immediately
try {
    $pid | Out-File -FilePath $pidFile -Encoding ascii -Force
    Write-Log "INFO" "PID file ecrit: $pidFile (PID: $pid)"
} catch {
    Write-Log "WARN" "Impossible d'ecrire le PID file: $($_.Exception.Message)"
}

# --------------------------------------------------
# Helper functions (unchanged from F030)
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
        message     = "Helper actif"
        helper_pid  = $pid
        timestamp   = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        version     = $helperVersion
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
    try {
        $existing = netsh interface portproxy show all | Select-String "0.0.0.0.*8011"
        if ($existing) {
            netsh interface portproxy delete v4tov4 listenport=$LanPort listenaddress=0.0.0.0 | Out-Null
        }
    } catch { }

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
    try {
        $Response.OutputStream.Write($buffer, 0, $buffer.Length)
    } finally {
        $Response.OutputStream.Close()
    }
}

function Send-Error {
    param($Response, $Code, $Message)
    $Response.StatusCode = $Code
    Send-JsonResponse $Response @{ success = $false; message = $Message }
}

# --------------------------------------------------
# Global try/catch — server setup
# --------------------------------------------------
try {
    $listener = New-Object System.Net.HttpListener
    $prefix = "http://${BindAddress}:${Port}/"
    $listener.Prefixes.Add($prefix)
    $listener.Start()
    Write-Log "INFO" "Helper demarre sur $prefix"
    Write-Log "INFO" "  Version: $helperVersion"
    Write-Log "INFO" "  Endpoints: GET /status, POST /sync, POST /restart-app, POST /test, POST /disable"

    try {
        while ($listener.IsListening) {
            try {
                $context = $listener.GetContext()
                $req = $context.Request
                $res = $context.Response

                $origin = $req.Headers["Origin"]
                $path = $req.Url.AbsolutePath.TrimEnd("/")
                $method = $req.HttpMethod

                Write-Log "DEBUG" "Requete: $method $path (Origin: $origin)"

                # CORS headers on every response
                Add-CorsHeaders -Response $res -Origin $origin

                # OPTIONS preflight — immediate 204, no action
                if ($method -eq "OPTIONS") {
                    $res.StatusCode = 204
                    $res.ContentLength64 = 0
                    $res.Close()
                    Write-Log "DEBUG" "OPTIONS 204 → $path"
                    continue
                }

                # Validate Origin (not for OPTIONS which was already handled)
                $allowedOrigins = @("http://localhost:8010", "http://127.0.0.1:8010", $null, "")
                if ($origin -and ($allowedOrigins -notcontains $origin)) {
                    Send-Error $res 403 "Origine non autorisee: $origin"
                    $res.Close()
                    Write-Log "WARN" "403 → $method $path (Origin: $origin)"
                    continue
                }

                # Route handling — per-request try/catch ensures response always sent
                try {
                    if ($path -eq "/status" -and $method -eq "GET") {
                        $data = Get-Status
                        Send-JsonResponse $res $data
                        Write-Log "DEBUG" "200 GET /status (${method}s)"
                    } elseif ($path -eq "/sync" -and $method -eq "POST") {
                        $data = Invoke-Sync
                        Send-JsonResponse $res $data
                        Write-Log "INFO" "200 POST /sync"
                    } elseif ($path -eq "/restart-app" -and $method -eq "POST") {
                        $data = Invoke-RestartApp
                        Send-JsonResponse $res $data
                        Write-Log "INFO" "200 POST /restart-app"
                    } elseif ($path -eq "/test" -and $method -eq "POST") {
                        $data = Invoke-Test
                        Send-JsonResponse $res $data
                        Write-Log "DEBUG" "200 POST /test"
                    } elseif ($path -eq "/disable" -and $method -eq "POST") {
                        $data = Invoke-Disable
                        Send-JsonResponse $res $data
                        Write-Log "INFO" "200 POST /disable"
                    } elseif ($path -eq "" -or $path -eq "/") {
                        Send-JsonResponse $res @{ success = $true; message = "TAf LAN Helper en ecoute." }
                        Write-Log "DEBUG" "200 GET /"
                    } else {
                        Send-Error $res 404 "Endpoint non trouve: $method $path"
                        Write-Log "WARN" "404 → $method $path"
                    }
                } catch {
                    Write-Log "ERROR" "Erreur route $method $path: $($_.Exception.Message)"
                    try {
                        if ($res -and $res.OutputStream -and $res.OutputStream.CanWrite) {
                            Send-Error $res 500 "Erreur interne: $($_.Exception.Message)"
                        }
                    } catch {
                        Write-Log "ERROR" "Impossible d'envoyer la reponse d'erreur: $($_.Exception.Message)"
                    }
                }

                # Ensure response is closed
                try {
                    $res.Close()
                } catch {
                    Write-Log "ERROR" "Erreur Close: $($_.Exception.Message)"
                }
            } catch {
                Write-Log "ERROR" "Erreur lors du traitement de la requete: $($_.Exception.Message)"
            }
        }
    } finally {
        Write-Log "INFO" "Arret du listener..."
        try { $listener.Stop() } catch { Write-Log "WARN" "Erreur Stop: $($_.Exception.Message)" }
        try { $listener.Close() } catch { Write-Log "WARN" "Erreur Close listener: $($_.Exception.Message)" }
        Write-Log "INFO" "Listener arrete"
    }
} catch {
    Write-Log "ERROR" "Erreur fatale au demarrage: $($_.Exception.Message)"
    exit 1
} finally {
    # Clean up PID file
    try {
        if (Test-Path $pidFile) {
            Remove-Item $pidFile -Force
            Write-Log "INFO" "PID file supprime: $pidFile"
        }
    } catch {
        Write-Log "WARN" "Impossible de supprimer le PID file: $($_.Exception.Message)"
    }
    Write-Log "INFO" "Helper termine (PID: $pid)"
}
