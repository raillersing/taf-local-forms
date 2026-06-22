import json
import os
import shutil
from pathlib import Path


def _settings_file():
    return Path(os.environ.get("DATABASE_PATH", "/app/data/db.sqlite3")).parent / "settings.env"

WHITELIST_EDITABLE = {
    "TAF_HOST_PORT",
    "TAF_LAN_HOST",
    "ALLOWED_HOSTS",
    "CSRF_TRUSTED_ORIGINS",
    "TIME_ZONE",
}

WHITELIST_READONLY = {
    "DEBUG",
    "DATABASE_PATH",
}

DEFAULT_EDITABLE = {
    "TAF_HOST_PORT": "8010",
    "TAF_LAN_HOST": "",
    "ALLOWED_HOSTS": "localhost,127.0.0.1,[::1]",
    "CSRF_TRUSTED_ORIGINS": "http://localhost:8010,http://127.0.0.1:8010",
    "TIME_ZONE": "Indian/Antananarivo",
}


def _load_settings_file():
    sf = _settings_file()
    if sf.exists():
        try:
            with open(sf) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_filtered_settings():
    stored = _load_settings_file()
    editable = {}
    for key in sorted(WHITELIST_EDITABLE):
        value = os.environ.get(key) or stored.get(key) or DEFAULT_EDITABLE.get(key, "")
        editable[key] = value
    readonly = {}
    for key in sorted(WHITELIST_READONLY):
        value = os.environ.get(key, "")
        readonly[key] = value
    has_secret = bool(os.environ.get("SECRET_KEY"))
    return {
        "editable": editable,
        "readonly": readonly,
        "has_secret_key": has_secret,
    }


def _validate_ipv4_or_empty(value):
    value = value.strip()
    if not value:
        return True, ""
    parts = value.split(".")
    if len(parts) != 4:
        return False, "Doit être une adresse IPv4 valide (ex: 192.168.0.102) ou vide."
    for p in parts:
        if not p.isdigit() or not (0 <= int(p) <= 255):
            return False, "Doit être une adresse IPv4 valide (ex: 192.168.0.102) ou vide."
    return True, value


def _validate_port(value):
    value = value.strip()
    if not value.isdigit():
        return False, "Doit être un nombre."
    port = int(value)
    if port < 1024 or port > 65535:
        return False, "Doit être entre 1024 et 65535."
    return True, value


def _validate_allowed_hosts(value):
    value = value.strip()
    if value == "*":
        return False, "ALLOWED_HOSTS=* est interdit pour la sécurité."
    if not value:
        return False, "Ne peut pas être vide."
    return True, value


def _validate_csrf_origins(value):
    value = value.strip()
    if not value:
        return False, "Ne peut pas être vide."
    origins = [o.strip() for o in value.split(",")]
    for origin in origins:
        if not (origin.startswith("http://") or origin.startswith("https://")):
            return False, f"Chaque origine doit commencer par http:// ou https:// : {origin}"
    return True, value


def _validate_timezone(value):
    value = value.strip()
    if not value or "/" not in value:
        return False, "Doit être un fuseau horaire valide (ex: Indian/Antananarivo)."
    return True, value


VALIDATORS = {
    "TAF_HOST_PORT": _validate_port,
    "TAF_LAN_HOST": _validate_ipv4_or_empty,
    "ALLOWED_HOSTS": _validate_allowed_hosts,
    "CSRF_TRUSTED_ORIGINS": _validate_csrf_origins,
    "TIME_ZONE": _validate_timezone,
}


def apply_setting(key, value):
    if key not in WHITELIST_EDITABLE:
        return False, "Ce champ n'est pas modifiable."
    validator = VALIDATORS.get(key)
    if validator:
        ok, msg = validator(value)
        if not ok:
            return False, msg
    current = {}
    sf = _settings_file()
    if sf.exists():
        try:
            with open(sf) as f:
                current = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    current[key] = value.strip() if isinstance(value, str) else value
    backup = sf.with_suffix(".env.bak")
    try:
        sf.parent.mkdir(parents=True, exist_ok=True)
        if sf.exists():
            shutil.copy2(sf, backup)
        with open(sf, "w") as f:
            json.dump(current, f, indent=2)
    except OSError as e:
        return False, f"Impossible d'écrire la configuration : {e}"
    return True, "Valeur enregistrée."


def load_settings_env():
    sf = _settings_file()
    if sf.exists():
        try:
            with open(sf) as f:
                overrides = json.load(f)
            for key, value in overrides.items():
                os.environ[key] = str(value)
        except (json.JSONDecodeError, OSError):
            pass
