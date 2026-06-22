import os
import socket
import subprocess
from urllib.parse import urlparse


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
        return 16 <= n <= 31
    return False


def get_network_access_context(request):
    taf_host_port = os.environ.get("TAF_HOST_PORT", "")
    taf_lan_host = os.environ.get("TAF_LAN_HOST", "").strip()
    public_lan_host = os.environ.get("PUBLIC_LAN_HOST", "").strip()

    explicit_host = taf_lan_host or public_lan_host or ""

    current_host_from_request = request.get_host()
    parsed = urlparse(f"//{current_host_from_request}")
    current_host = parsed.hostname or current_host_from_request
    current_port = str(parsed.port) if parsed.port else ""

    raw_candidates = _get_ip_candidates()
    detected_ip_candidates = [ip for ip in raw_candidates if not _is_docker_ip(ip)]
    detected_ip_candidates = detected_ip_candidates[:5]

    has_detected_ips = bool(detected_ip_candidates)

    if explicit_host:
        recommended_host = explicit_host
    elif current_host not in ("127.0.0.1", "localhost", "0.0.0.0", ""):
        recommended_host = current_host
    elif has_detected_ips:
        recommended_host = detected_ip_candidates[0]
    else:
        recommended_host = ""

    port = taf_host_port or current_port or "8000"

    has_lan_host = bool(explicit_host)

    def url_for(path):
        if recommended_host:
            return f"http://{recommended_host}:{port}{path}"
        url = f"http://localhost:{port}{path}"
        return url

    warnings = []

    if not has_lan_host:
        if not has_detected_ips:
            warnings.append(
                "IP locale non configurée. Aucune IP candidate détectée automatiquement. "
                "Configure TAF_LAN_HOST dans l'interface Configuration réseau."
            )
        else:
            warnings.append(
                "IP locale non configurée. Les liens ci-dessous utilisent une IP détectée. "
                "Configure TAF_LAN_HOST dans Configuration réseau pour une adresse stable."
            )

    if current_host in ("127.0.0.1", "localhost", "0.0.0.0"):
        if not has_lan_host:
            warnings.append(
                "L'adresse actuelle ({}) ne fonctionne que sur cet ordinateur. "
                "Les élèves ne peuvent pas l'utiliser depuis leur téléphone.".format(current_host)
            )

    if recommended_host and _is_docker_ip(recommended_host):
        warnings.append(
            "L'adresse actuelle ({}) ressemble à une IP Docker. "
            "Les élèves ne pourront probablement pas y accéder.".format(recommended_host)
        )

    # ── LAN diagnostics ────────────────────────────────────
    under_wsl = _is_wsl()
    wsl_gateway = _detect_wsl_gateway() if under_wsl else ""

    return {
        "current_host": current_host,
        "current_port": current_port,
        "configured_host": explicit_host or "",
        "configured_port": taf_host_port or "",
        "has_lan_host": has_lan_host,
        "detected_ip_candidates": detected_ip_candidates,
        "recommended_host": recommended_host,
        "port": port,
        "student_form_url": url_for("/"),
        "module_2_url": url_for("/module-2/"),
        "module_3_url": url_for("/module-3/"),
        "module_4_url": url_for("/module-4/"),
        "cockpit_url": url_for("/dashboard/"),
        "dashboard_network_url": url_for("/dashboard/network/"),
        "dashboard_settings_url": url_for("/dashboard/settings/"),
        "dashboard_module_2_url": url_for("/dashboard/module-2/"),
        "dashboard_module_3_url": url_for("/dashboard/module-3/"),
        "dashboard_module_4_url": url_for("/dashboard/module-4/"),
        "csv_module_2_url": url_for("/dashboard/export/module-2.csv"),
        "csv_module_3_url": url_for("/dashboard/export/module-3.csv"),
        "csv_module_4_url": url_for("/dashboard/export/module-4.csv"),
        "admin_url": url_for("/admin/"),
        "warnings": warnings,
        "under_wsl": under_wsl,
        "wsl_gateway": wsl_gateway,
    }
