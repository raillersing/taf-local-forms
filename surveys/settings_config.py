import json
import os
import re
import shutil
from pathlib import Path

SETTINGS_FILE = Path(os.environ.get("DATABASE_PATH", "/app/data/db.sqlite3")).parent / "settings.env"

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

SENSITIVE_KEYS_PATTERNS = [
    re.compile(r"SECRET", re.IGNORECASE),
    re.compile(r"KEY", re.IGNORECASE),
    re.compile(r"PASSWORD", re.IGNORECASE),
    re.compile(r"TOKEN", re.IGNORECASE),
    re.compile(r"API", re.IGNORECASE),
    re.compile(r"PRIVATE", re.IGNORECASE),
    re.compile(r"DATABASE_URL", re.IGNORECASE),
]


def _is_sensitive(key):
    return any(p.search(key) for p in SENSITIVE_KEYS_PATTERNS)


def get_filtered_settings():
    result = {"editable": {}, "readonly": {}, "sensitive": {}}
    for key, value in sorted(os.environ.items()):
        if key in WHITELIST_EDITABLE:
            result["editable"][key] = value
        elif key in WHITELIST_READONLY:
            result["readonly"][key] = value
        elif _is_sensitive(key):
            result["sensitive"][key] = bool(value)
    if "SECRET_KEY" not in result["sensitive"]:
        result["sensitive"]["SECRET_KEY"] = bool(os.environ.get("SECRET_KEY"))
    return result


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
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                current = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    current[key] = value.strip() if isinstance(value, str) else value
    backup = SETTINGS_FILE.with_suffix(".env.bak")
    try:
        if SETTINGS_FILE.exists():
            shutil.copy2(SETTINGS_FILE, backup)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(current, f, indent=2)
    except OSError as e:
        return False, f"Impossible d'écrire la configuration : {e}"
    return True, "Valeur enregistrée."


def load_settings_env():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                overrides = json.load(f)
            for key, value in overrides.items():
                os.environ[key] = str(value)
        except (json.JSONDecodeError, OSError):
            pass
