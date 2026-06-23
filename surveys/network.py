import os
import socket
import subprocess
from urllib.parse import urlparse


PRIVATE_IP_PREFIXES = (
    "192.168.",
    "10.",
)

PRIVATE_172_START = 16
PRIVATE_172_END = 31

EXCLUDED_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0", "[::1]", ""}


def _detect_wsl_gateway():
    try:
        out = subprocess.check_output(
            ["ip", "route", "show"], text=True, stderr=subprocess.DEVNULL, timeout=5
        )
        for line in out.splitlines():
            parts = line.strip().split()
            if parts and parts[0] == "default":
                return parts[2]
    except Exception:
        pass
    return ""


def _is_wsl():
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def _get_ip_candidates():
    candidates = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
            addr = info[4][0]
            if not addr.startswith("127.") and addr != "0.0.0.0":
                candidates.add(addr)
    except OSError:
        pass
    return sorted(candidates)


def _is_docker_ip(ip):
    parts = ip.split(".")
    if len(parts) >= 2 and parts[0] == "172" and parts[1].isdigit():
        n = int(parts[1])
        return PRIVATE_172_START <= n <= PRIVATE_172_END
    return False


def _is_private_ip(host):
    if host.startswith(PRIVATE_IP_PREFIXES):
        return True
    if host.startswith("172."):
        parts = host.split(".")
        if len(parts) >= 2 and parts[1].isdigit():
            n = int(parts[1])
            return PRIVATE_172_START <= n <= PRIVATE_172_END
    return False


def _parse_host_port(host_string):
    parsed = urlparse(f"//{host_string}")
    hostname = parsed.hostname or host_string
    port = str(parsed.port) if parsed.port else ""
    return hostname, port


def get_network_access_context(request):
    taf_host_port = os.environ.get("TAF_HOST_PORT", "")
    taf_lan_host = os.environ.get("TAF_LAN_HOST", "").strip()
    public_lan_host = os.environ.get("PUBLIC_LAN_HOST", "").strip()

    configured_host = taf_lan_host or public_lan_host or ""
    configured_port = taf_host_port or ""

    current_request_host_raw = request.get_host()
    current_request_host, current_request_port = _parse_host_port(current_request_host_raw)
    current_request_is_lan = _is_private_ip(current_request_host) and current_request_host not in EXCLUDED_HOSTS

    raw_candidates = _get_ip_candidates()
    detected_ip_candidates = [ip for ip in raw_candidates if not _is_docker_ip(ip)]
    detected_ip_candidates = detected_ip_candidates[:5]

    has_detected_ips = bool(detected_ip_candidates)

    # Determine recommended LAN host and source
    if current_request_is_lan:
        recommended_host = current_request_host
        if current_request_port:
            recommended_port_num = current_request_port
        elif configured_port:
            recommended_port_num = configured_port
        else:
            recommended_port_num = "8010"
        lan_host_source = "request"
    elif configured_host:
        recommended_host = configured_host
        recommended_port_num = configured_port or "8010"
        lan_host_source = "settings"
    elif has_detected_ips:
        recommended_host = detected_ip_candidates[0]
        recommended_port_num = configured_port or "8010"
        lan_host_source = "candidate"
    else:
        recommended_host = ""
        recommended_port_num = configured_port or "8010"
        lan_host_source = "missing"

    # Port for URLs: use configured port, or current request port, or default
    port = configured_port or current_request_port or "8000"

    has_lan_host = bool(configured_host)

    # Check if configured host is stale (differs from current request LAN host)
    lan_host_stale = (
        has_lan_host
        and current_request_is_lan
        and current_request_host != configured_host
    )

    recommended_student_base_url = (
        f"http://{recommended_host}:{recommended_port_num}"
        if recommended_host
        else ""
    )

    def url_for(path):
        if recommended_host:
            return f"http://{recommended_host}:{port}{path}"
        return f"http://localhost:{port}{path}"

    warnings = []

    if not has_lan_host:
        if not has_detected_ips:
            warnings.append(
                "IP locale non configurée. Aucune IP candidate détectée automatiquement. "
                "Configure TAF_LAN_HOST dans l'interface Configuration réseau."
            )
        elif not current_request_is_lan:
            warnings.append(
                "IP locale non configurée. Les liens ci-dessous utilisent une IP détectée. "
                "Configure TAF_LAN_HOST dans Configuration réseau pour une adresse stable."
            )

    if current_request_host in ("127.0.0.1", "localhost", "0.0.0.0") and not has_lan_host:
        warnings.append(
            "L'adresse actuelle ({}) ne fonctionne que sur cet ordinateur. "
            "Les élèves ne peuvent pas l'utiliser depuis leur téléphone.".format(current_request_host)
        )

    if recommended_host and _is_docker_ip(recommended_host):
        warnings.append(
            "L'adresse actuelle ({}) ressemble à une IP Docker. "
            "Les élèves ne pourront probablement pas y accéder.".format(recommended_host)
        )

    if lan_host_stale:
        warnings.append(
            "L'IP configurée ({}) diffère de l'adresse actuelle ({}). "
            "Mets à jour la configuration pour utiliser l'adresse actuelle.".format(
                configured_host, current_request_host
            )
        )

    # LAN diagnostics
    under_wsl = _is_wsl()
    wsl_gateway = _detect_wsl_gateway() if under_wsl else ""

    return {
        "current_host": current_request_host,
        "current_port": current_request_port,
        "current_request_host": current_request_host,
        "current_request_is_lan": current_request_is_lan,
        "configured_host": configured_host or "",
        "configured_port": configured_port or "",
        "configured_lan_host": configured_host or "",
        "configured_lan_port": configured_port or "",
        "has_lan_host": has_lan_host,
        "detected_ip_candidates": detected_ip_candidates,
        "recommended_host": recommended_host,
        "recommended_port": recommended_port_num,
        "recommended_lan_host": recommended_host,
        "recommended_lan_port": recommended_port_num,
        "recommended_student_base_url": recommended_student_base_url,
        "lan_host_source": lan_host_source,
        "lan_host_stale": lan_host_stale,
        "port": port,
        "student_form_url": url_for("/"),
        "module_2_url": url_for("/module-2/"),
        "module_3_url": url_for("/module-3/"),
        "module_4_url": url_for("/module-4/"),
        "module_5_url": url_for("/module-5/"),
        "cockpit_url": url_for("/dashboard/"),
        "dashboard_network_url": url_for("/dashboard/network/"),
        "dashboard_settings_url": url_for("/dashboard/settings/"),
        "dashboard_module_2_url": url_for("/dashboard/module-2/"),
        "dashboard_module_3_url": url_for("/dashboard/module-3/"),
        "dashboard_module_4_url": url_for("/dashboard/module-4/"),
        "dashboard_module_5_url": url_for("/dashboard/module-5/"),
        "csv_module_2_url": url_for("/dashboard/export/module-2.csv"),
        "csv_module_3_url": url_for("/dashboard/export/module-3.csv"),
        "csv_module_4_url": url_for("/dashboard/export/module-4.csv"),
        "csv_module_5_url": url_for("/dashboard/export/module-5.csv"),
        "admin_url": url_for("/admin/"),
        "warnings": warnings,
        "under_wsl": under_wsl,
        "wsl_gateway": wsl_gateway,
    }
