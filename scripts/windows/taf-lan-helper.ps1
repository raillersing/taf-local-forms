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
    [int]$LanPort = 8011,
    [string]$WslDistribution = $env:TAF_WSL_DISTRO,
    [string]$WslProjectPath = $env:TAF_WSL_PROJECT_PATH
)

$ErrorActionPreference = "Stop"

# --------------------------------------------------
# Log / PID setup
# --------------------------------------------------
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$wslToolsPath = Join-Path $scriptDir "taf-lan-wsl.ps1"
if (-not (Test-Path $wslToolsPath)) {
    throw "Utilitaire WSL introuvable: $wslToolsPath"
}
. $wslToolsPath
$logDir = Join-Path $projectRoot "logs\windows"
if (-not (Test-Path $logDir)) {
    $null = New-Item -ItemType Directory -Path $logDir -Force
}
$logFile = Join-Path $logDir "taf-lan-helper.log"
$pidFile = Join-Path $logDir "taf-lan-helper.pid"
$helperVersion = "1.1.0"
$tokenBytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($tokenBytes)
$controlToken = [Convert]::ToBase64String($tokenBytes)

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
# Network detection helpers
# --------------------------------------------------
function Test-PrivateIPv4 {
    param([string]$IpAddress)
    $address = $null
    if (-not [System.Net.IPAddress]::TryParse($IpAddress, [ref]$address)) { return $false }
    if ($address.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) { return $false }
    $bytes = $address.GetAddressBytes()
    return (
        $bytes[0] -eq 10 -or
        ($bytes[0] -eq 192 -and $bytes[1] -eq 168) -or
        ($bytes[0] -eq 172 -and $bytes[1] -ge 16 -and $bytes[1] -le 31)
    )
}

function Get-ActiveLanDetails {
    $candidates = @(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        (Test-PrivateIPv4 $_.IPAddress) -and
        $_.IPAddress -notlike "127.*" -and
        $_.IPAddress -notlike "169.254.*" -and
        $_.InterfaceAlias -notmatch "(?i)vEthernet|Docker|WSL|Hyper-V|Default Switch"
    } | ForEach-Object {
        $ip = $_
        $hasGateway = Get-NetRoute -DestinationPrefix "0.0.0.0/0" |
            Where-Object { $_.InterfaceIndex -eq $ip.InterfaceIndex -and $_.NextHop -ne "0.0.0.0" }
        $prio = if ($hasGateway) { 0 } else { 1 }
        [PSCustomObject]@{
            IPAddress      = $ip.IPAddress
            InterfaceAlias = $ip.InterfaceAlias
            InterfaceIndex = $ip.InterfaceIndex
            Gateway        = if ($hasGateway) { ($hasGateway | Select-Object -First 1).NextHop } else { $null }
            Priority       = $prio
            HasGateway     = [bool]$hasGateway
        }
    } | Sort-Object Priority)

    $withGateway = $candidates | Where-Object { $_.HasGateway }
    if ($withGateway) { $candidates = $withGateway }
    if ($candidates.Count -ge 1) { return $candidates[0].IPAddress }
    return $null
}

function Get-ActiveLanIp {
    $details = Get-ActiveLanDetails
    if ($details) { return $details.IPAddress }
    return $null
}

function Get-PortproxyStatus {
    try {
        $output = @(netsh interface portproxy show all)
        $rules = @()
        foreach ($line in $output) {
            if ($line -match '^\s*(\S+)\s+(\d+)\s+(\S+)\s+(\d+)\s*$') {
                $rules += [PSCustomObject]@{
                    listen_address  = $Matches[1]
                    listen_port     = [int]$Matches[2]
                    connect_address = $Matches[3]
                    connect_port    = [int]$Matches[4]
                }
            }
        }
        $matching = @($rules | Where-Object {
            $_.listen_address -eq "0.0.0.0" -and
            $_.listen_port -eq $LanPort -and
            $_.connect_address -eq "127.0.0.1" -and
            $_.connect_port -eq $DockerPort
        })
        $conflicts = @($rules | Where-Object {
            $_.listen_port -eq $LanPort -and $_ -notin $matching
        })
        return @{
            exists = ($matching.Count -gt 0)
            conflict = ($conflicts.Count -gt 0)
            rules = $rules
            conflicts = $conflicts
            details = $output
        }
    } catch {
        return @{ exists = $false; conflict = $false; rules = @(); conflicts = @(); details = ($_.Exception.Message) }
    }
}

function Get-FirewallStatus {
    try {
        $ruleName = "TAf Local Forms - Port 8011"
        $rules = @(Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)
        if ($rules.Count -gt 0) {
            $validRules = @($rules | Where-Object {
                $portFilter = $_ | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue
                $_.Direction -eq 'Inbound' -and
                $_.Action -eq 'Allow' -and
                $_.Enabled -eq 'True' -and
                $portFilter.Protocol -eq 'TCP' -and
                @($portFilter.LocalPort) -contains [string]$LanPort
            })
            return @{
                exists = $true
                enabled = ($validRules.Count -gt 0)
                conflict = ($validRules.Count -eq 0)
            }
        }
        return @{ exists = $false; enabled = $false; conflict = $false }
    } catch {
        return @{ exists = $false; enabled = $false; conflict = $false }
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

function Test-DjangoHost {
    param([string]$Ip)
    if (-not $Ip) { return $false }
    try {
        $headers = @{ Host = "$Ip`:$LanPort" }
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$DockerPort/" -Headers $headers -Method Head -TimeoutSec 5
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Get-Status {
    $lan = Get-ActiveLanDetails
    $lanIp = if ($lan) { $lan.IPAddress } else { $null }
    $localOk = Test-LocalApp
    $portproxy = Get-PortproxyStatus
    $firewall = Get-FirewallStatus
    $lanOk = if ($lanIp) { Test-LanUrl -Ip $lanIp } else { $false }
    $djangoAllowsIp = if ($lanIp) { Test-DjangoHost -Ip $lanIp } else { $false }

    $studentUrl = if ($lanIp) { "http://$lanIp`:$LanPort/" } else { $null }

    return @{
        success     = $true
        message     = "Helper actif"
        helper_pid  = $pid
        timestamp   = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        version     = $helperVersion
        control_token = $controlToken
        lan_ip      = $lanIp
        lan_interface = if ($lan) { $lan.InterfaceAlias } else { $null }
        lan_gateway = if ($lan) { $lan.Gateway } else { $null }
        student_url = $studentUrl
        local_ok    = $localOk
        portproxy   = $portproxy.exists
        firewall    = $firewall.exists
        portproxy_conflict = $portproxy.conflict
        firewall_conflict = $firewall.conflict
        lan_ok      = $lanOk
        helper_running = $true
        local_app_ok = $localOk
        portproxy_ok = $portproxy.exists
        firewall_ok = $firewall.exists -and $firewall.enabled
        django_allows_ip = $djangoAllowsIp
        student_url_ok = $lanOk
        diagnostics = @{
            local_port  = $DockerPort
            lan_port    = $LanPort
            helper_port = $Port
            portproxy_conflicts = $portproxy.conflicts
        }
    }
}

function Invoke-Sync {
    $lanIp = Get-ActiveLanIp
    if (-not $lanIp) {
        return @{ success = $false; message = "Aucune adresse LAN detectee." }
    }

    # Portproxy: ne jamais remplacer une regle concurrente.
    try {
        $portproxyStatus = Get-PortproxyStatus
        if ($portproxyStatus.conflict) {
            return @{
                success = $false
                message = "Conflit detecte sur le port LAN $LanPort : une autre regle portproxy existe."
                lan_ip = $lanIp
                portproxy_ok = $false
                portproxy_conflict = $true
                diagnostics = @{ portproxy = $false; conflict = $true; conflicts = $portproxyStatus.conflicts }
            }
        }
        if (-not $portproxyStatus.exists) {
            netsh interface portproxy delete v4tov4 listenport=$LanPort listenaddress=0.0.0.0 | Out-Null
            netsh interface portproxy add v4tov4 listenport=$LanPort listenaddress=0.0.0.0 connectport=$DockerPort connectaddress=127.0.0.1 | Out-Null
        }
        $proxyOk = $true
    } catch {
        $proxyOk = $false
        $proxyError = $_.Exception.Message
    }

    # Firewall
    try {
        $ruleName = "TAf Local Forms - Port 8011"
        $firewallStatus = Get-FirewallStatus
        if ($firewallStatus.conflict) {
            return @{
                success = $false
                message = "Conflit detecte dans la regle pare-feu '$ruleName'."
                lan_ip = $lanIp
                firewall_ok = $false
                firewall_conflict = $true
                diagnostics = @{ portproxy = $proxyOk; firewall = $false; conflict = $true }
            }
        }
        if (-not $firewallStatus.exists) {
            New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $LanPort -Action Allow | Out-Null
        }
        $fwOk = $true
    } catch {
        $fwOk = $false
        $fwError = $_.Exception.Message
    }

    # WSL sync
    try {
        $wslContext = Get-TafWslContext -ScriptDirectory $scriptDir -WslDistribution $WslDistribution -WslProjectPath $WslProjectPath
        $wslResult = Invoke-TafWslCompose -Context $wslContext -ComposeArguments @(
            "exec", "-T", "web", "python", "manage.py", "sync_lan_settings",
            "--lan-host", $lanIp, "--lan-port", $LanPort
        )
        $wslOk = ($wslResult.ExitCode -eq 0)
        $wslMessage = $wslResult.Output
    } catch {
        $wslOk = $false
        $wslMessage = $_.Exception.Message
    }

    $studentUrl = "http://${lanIp}:${LanPort}/"
    $verification = Get-Status
    $ok = $proxyOk -and $fwOk -and $wslOk -and $verification.student_url_ok

    return @{
        success     = $ok
        message     = if ($ok) { "Acces LAN configure et verifie sur ${lanIp}:${LanPort}." } else { "Configuration incomplete : verifiez le portproxy, le pare-feu, Django et l'URL eleves." }
        lan_ip      = $lanIp
        student_url = $studentUrl
        diagnostics = @{
            portproxy = $proxyOk
            firewall  = $fwOk
            wsl_sync  = $wslOk
            verification = $verification.student_url_ok
        }
        local_app_ok = $verification.local_app_ok
        portproxy_ok = $verification.portproxy_ok
        firewall_ok = $verification.firewall_ok
        django_allows_ip = $verification.django_allows_ip
        student_url_ok = $verification.student_url_ok
    }
}

function Invoke-Disable {
    $proxyOk = $true
    $firewallOk = $true
    try {
        $portproxyStatus = Get-PortproxyStatus
        if ($portproxyStatus.conflict) {
            $proxyOk = $false
        } elseif ($portproxyStatus.exists) {
            netsh interface portproxy delete v4tov4 listenport=$LanPort listenaddress=0.0.0.0 | Out-Null
        }
    } catch { $proxyOk = $false }

    try {
        $ruleName = "TAf Local Forms - Port 8011"
        $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        if ($existingRule) {
            Remove-NetFirewallRule -DisplayName $ruleName
        }
    } catch { $firewallOk = $false }

    $ok = $proxyOk -and $firewallOk
    return @{
        success = $ok
        message = if ($ok) { "Acces LAN desactive. Portproxy et regle pare-feu supprimes." } else { "Desactivation incomplete ou conflit detecte : aucune regle concurrente n'a ete supprimee." }
        diagnostics = @{ portproxy_removed = $proxyOk; firewall_removed = $firewallOk; portproxy_conflict = ($portproxyStatus.conflict) }
    }
}

function Invoke-Test {
    $lanIp = Get-ActiveLanIp
    $localOk = Test-LocalApp
    $lanOk = if ($lanIp) { Test-LanUrl -Ip $lanIp } else { $false }
    $djangoOk = if ($lanIp) { Test-DjangoHost -Ip $lanIp } else { $false }

    $studentUrl = if ($lanIp) { "http://$lanIp`:$LanPort/" } else { $null }

    return @{
        success     = $lanOk
        message     = if ($lanOk) { "URL eleves accessible : $studentUrl" } else { "URL eleves inaccessible. Verifiez la configuration LAN." }
        lan_ip      = $lanIp
        student_url = $studentUrl
        local_app_ok = $localOk
        django_allows_ip = $djangoOk
        student_url_ok = $lanOk
        diagnostics = @{
            local_accessible = $localOk
            lan_accessible   = $lanOk
        }
    }
}

function Invoke-RestartApp {
    try {
        $wslContext = Get-TafWslContext -ScriptDirectory $scriptDir -WslDistribution $WslDistribution -WslProjectPath $WslProjectPath
        $wslResult = Invoke-TafWslCompose -Context $wslContext -ComposeArguments @("restart", "web")
        if ($wslResult.ExitCode -ne 0) {
            return @{ success = $false; message = "Le redemarrage Docker a echoue."; output = $wslResult.Output }
        }
        return @{ success = $true; message = "Application redemarree."; output = $wslResult.Output }
    } catch {
        return @{ success = $false; message = "Erreur lors du redemarrage: $($_.Exception.Message)" }
    }
}

function Invoke-OpenHelperFolder {
    try {
        Start-Process -FilePath "explorer.exe" -ArgumentList @($scriptDir) -ErrorAction Stop
        return @{ success = $true; message = "Le dossier des commandes Windows a ete ouvert."; folder = $scriptDir }
    } catch {
        return @{ success = $false; message = "Impossible d'ouvrir le dossier Windows : $($_.Exception.Message)" }
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
    $Response.Headers.Add("Access-Control-Allow-Headers", "Content-Type, X-TAF-Helper-Token")
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
    Write-Log "INFO" "  Endpoints: GET /status, POST /sync, POST /restart-app, POST /test, POST /disable, POST /open-folder"

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

                if ($method -eq "POST" -and $req.Headers["X-TAF-Helper-Token"] -ne $controlToken) {
                    Send-Error $res 403 "Jeton helper absent ou invalide."
                    $res.Close()
                    Write-Log "WARN" "403 → $method $path (jeton invalide)"
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
                    } elseif ($path -eq "/open-folder" -and $method -eq "POST") {
                        $data = Invoke-OpenHelperFolder
                        Send-JsonResponse $res $data
                        Write-Log "INFO" "200 POST /open-folder"
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
                    Write-Log "ERROR" "Erreur route $method ${path}: $($_.Exception.Message)"
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
