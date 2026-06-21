import os
import socket
from urllib.parse import urlparse


def _get_ip_candidates():
    """Collect non-loopback, non-docker IPv4 addresses from local interfaces."""
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

    if explicit_host:
        recommended_host = explicit_host
    elif current_host not in ("127.0.0.1", "localhost", "0.0.0.0"):
        recommended_host = current_host
    elif detected_ip_candidates:
        recommended_host = detected_ip_candidates[0]
    else:
        recommended_host = "<IP_DU_LAPTOP>"

    port = taf_host_port or current_port or "8000"

    def url_for(path):
        return f"http://{recommended_host}:{port}{path}"

    warnings = []

    if current_host in ("127.0.0.1", "localhost", "0.0.0.0"):
        warnings.append(
            "L'adresse actuelle ({}) ne fonctionne que sur cet ordinateur. "
            "Les élèves ne peuvent pas l'utiliser depuis leur téléphone.".format(current_host)
        )
        if not explicit_host:
            warnings.append(
                "Ajoute TAF_LAN_HOST=<IP_DU_LAPTOP> dans .env "
                "pour que la page affiche automatiquement la bonne adresse."
            )

    if _is_docker_ip(recommended_host):
        warnings.append(
            "L'adresse recommandée ({}) ressemble à une IP Docker. "
            "Les élèves ne pourront probablement pas y accéder.".format(recommended_host)
        )

    if not explicit_host and not detected_ip_candidates:
        warnings.append(
            "Aucune IP locale candidate détectée automatiquement. "
            "Renseigne TAF_LAN_HOST=<IP_DU_LAPTOP> dans .env."
        )

    return {
        "current_host": current_host,
        "current_port": current_port,
        "configured_host": explicit_host or "",
        "configured_port": taf_host_port or "",
        "detected_ip_candidates": detected_ip_candidates,
        "recommended_host": recommended_host,
        "port": port,
        "student_form_url": url_for("/module-2/"),
        "dashboard_url": url_for("/dashboard/module-2/"),
        "csv_export_url": url_for("/dashboard/export/module-2.csv"),
        "admin_url": url_for("/admin/"),
        "warnings": warnings,
    }
