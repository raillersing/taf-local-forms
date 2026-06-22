# Guide de dépannage réseau — WSL / Windows

Ce document explique comment diagnostiquer et résoudre les problèmes d'accès LAN
pour **TAf Local Forms** lorsque l'application tourne sous Docker dans WSL2.

> **But :** permettre aux élèves connectés sur le même Wi-Fi / hotspot d'accéder au
> formulaire depuis leur téléphone via `http://<IP_DU_LAPTOP>:8011/` (**port LAN `8011`**).

> **Depuis F023** : le script `taf-lan-sync.ps1` configure automatiquement un portproxy `8011→8010`, évitant les conflits avec d'autres services.

---

## 1. Diagnostic rapide

### Depuis WSL (lecture seule)

```sh
bash scripts/dev/taf-lan-diagnose
```

Ce script vérifie :
- Environnement WSL
- IP LAN de WSL
- Statut Docker
- Mapping de port
- Accessibilité locale de l'application
- Valeurs `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS`

### Depuis Windows (PowerShell)

```powershell
.\scripts\windows\taf-lan-show-status.ps1
```

Ce script vérifie (lecture seule) :
- Adresses IP de Windows
- Règles de pare-feu sur les ports 8010 et 8011
- Configuration portproxy (8011→8010)
- Profil réseau (Privé / Public)
- Test de connectivité localhost:8010

### Synchronisation complète (PowerShell Admin)

```powershell
.\scripts\windows\taf-lan-sync.ps1
```

Ce script détecte automatiquement l'IPv4 du Wi-Fi, configure le portproxy `8011→8010`, crée la règle pare-feu pour `8011`, et synchronise l'application Django.

Installation en tâche planifiée (logon automatique) :

```powershell
.\scripts\windows\taf-lan-install-auto-sync.ps1
```

---

## 2. Problèmes courants et solutions

### 2.1 Pare-feu Windows bloque le port 8010

**Symptôme :** l'application répond sur `http://localhost:8010/` depuis Windows
mais pas depuis un autre appareil sur le LAN.

**Solution :** Ouvrir le port dans le pare-feu Windows (PowerShell Admin) :

```powershell
.\scripts\windows\taf-lan-open-port.ps1
```

Ou manuellement :

```
Windows + R → wf.msc → Règles entrantes → Nouvelle règle → Port → TCP → 8010
```

### 2.2 Profil réseau en « Public »

**Symptôme :** connexions entrantes bloquées par Windows même avec la règle pare-feu.

**Solution :**
1. `Paramètres > Réseau et Internet > Wi-Fi > Propriétés`
2. Définir « Profil réseau » sur **Privé**

### 2.3 WSL2 NAT — l'IP WSL n'est pas accessible depuis le LAN

**Symptôme :** `http://<WSL_IP>:8010/` ne répond que depuis WSL, pas depuis
un autre appareil même si le pare-feu est ouvert.

**Cause :** WSL2 utilise NAT. Docker Desktop crée un proxy de `0.0.0.0:8010`
vers le port WSL interne, mais si ce proxy ne fonctionne pas, les paquets
n'arrivent jamais à WSL.

**Solutions (par ordre de priorité) :**

0. **Utiliser le script automatique (PowerShell Admin) :**
   ```powershell
   .\scripts\windows\taf-lan-sync.ps1
   ```
   Ce script détecte l'IP Wi-Fi, configure le portproxy `8011→8010`, le pare-feu pour `8011`, et synchronise l'application Django.

1. **Docker Desktop gère déjà le port forwarding.** Vérifier avec :
   ```
   curl http://localhost:8010/   # depuis Windows
   ```
   Si ça répond, le proxy fonctionne.

2. **Ajouter un portproxy Windows (PowerShell Admin) :**
   ```powershell
   netsh interface portproxy add v4tov4 listenport=8011 listenaddress=0.0.0.0 connectport=8010 connectaddress=127.0.0.1
   ```
   Puis vérifier :
   ```powershell
   netsh interface portproxy show v4tov4
   ```

3. **Redémarrer Docker Desktop** (sans `-v`) :
   ```sh
   docker compose down
   docker compose up -d
   ```

### 2.4 AP Isolation / Client Isolation

**Symptôme :** les téléphones sont connectés au même Wi-Fi que l'ordinateur
mais n'arrivent pas à charger l'application.

**Cause :** le point d'accès (routeur / hotspot) isole les clients entre eux.

**Solutions :**
- Désactiver « AP Isolation » ou « Client Isolation » dans l'interface du routeur
- Utiliser un hotspot téléphone plutôt qu'un réseau WiFi public
- Si l'établissement scolaire a un réseau invité, demande l'accès ou utilise
  un hotspot 4G/5G personnel

### 2.5 ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS

**Symptôme :** erreur HTTP 400 « Bad Request » ou 403 « CSRF Failed ».

**Solution :** Ajouter l'IP du laptop dans le `.env` ou dans l'interface de
configuration réseau (`/dashboard/settings/`).

Exemple `.env` :
```env
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.42
CSRF_TRUSTED_ORIGINS=http://localhost:8010,http://127.0.0.1:8010,http://192.168.1.42:8011
```

Ou via l'interface web :
```
/dashboard/settings/ → Utiliser l'adresse actuelle (nouveau bouton F023)
```

---

## 3. Référence : architecture réseau

```
┌──────────────────────────────────────────────────────────┐
│  Windows 10/11                                           │
│  IP LAN: 192.168.1.42 (exemple)                          │
│                                                           │
│  ┌───────────────────┐      ┌─────────────────────────┐  │
│  │ Portproxy Windows  │      │ Docker Desktop          │  │
│  │ 0.0.0.0:8011 ─────┼──────┼─► 0.0.0.0:8010 ───────►│  │
│  └───────────────────┘      └─────────────────────────┘  │
│                                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │  WSL2                                              │   │
│  │  IP: 172.x.y.z (interne)                           │   │
│  │  Gateway: 172.x.0.1                                │   │
│  │                                                    │   │
│  │  ┌──────────────────┐                              │   │
│  │  │  Docker container │────► Gunicorn web:8000      │   │
│  │  └──────────────────┘                              │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
         │  http://192.168.1.42:8011/
         ▼  (même Wi-Fi / hotspot)
   ┌──────────────┐
   │  Téléphone    │
   │  élève        │
   │  192.168.1.50 │
   └──────────────┘
```

---

## 4. Scripts de diagnostic

| Script | Emplacement | Rôle |
|--------|-------------|------|
| `taf-lan-diagnose` | `scripts/dev/` | Diagnostic WSL (lecture seule) |
| `taf-lan-show-status.ps1` | `scripts/windows/` | Statut réseau Windows (lecture seule) — détecte IP, portproxy, pare-feu 8010/8011 |
| `taf-lan-open-port.ps1` | `scripts/windows/` | Ouvrir le pare-feu Windows (Admin requis) |
| `taf-lan-sync.ps1` | `scripts/windows/` | Synchronisation complète — détecte IP Wi-Fi, portproxy `8011→8010`, pare-feu `8011`, sync Django (Admin requis) |
| `taf-lan-install-auto-sync.ps1` | `scripts/windows/` | Installe une tâche planifiée Windows pour synchronisation automatique au logon (Admin requis) |

---

## 5. Vérification finale

Depuis WSL :
```sh
bash scripts/dev/taf-lan-diagnose
```

Depuis un téléphone sur le même Wi-Fi :
```
http://<IP_DU_LAPTOP>:8011/
```

La page d'accueil publique doit s'afficher.
