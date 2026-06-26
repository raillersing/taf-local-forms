# TAF Cockpit Projection

## 1. Objectif

F037M rapproche le cockpit formateur du Prototype 6 pour partager plus vite
l'accès élèves en séance locale, sans toucher aux modèles, aux migrations ou à
la logique métier des questionnaires.

## 2. Routes et pages concernées

- `/dashboard/` : cockpit formateur enrichi
- `/dashboard/projection/` : page de projection protégée
- `/dashboard/network/` : diagnostic réseau existant, réutilisé

## 3. Fonctionnement du QR local

- Le QR code est généré localement dans le navigateur à partir de l'URL élèves.
- Aucun CDN n'est utilisé.
- Le fichier vendor ajouté est `static/js/vendor/qrcode.js`.
- Source : `davidshimjs/qrcodejs`
- Licence annoncée dans le fichier source : MIT

## 4. Mode projection

- La page projection affiche une URL élèves en grand format.
- Elle affiche aussi un QR code plus large pour la salle.
- Un bouton active le plein écran via `requestFullscreen()` si disponible.
- Si l'API n'est pas disponible, la page reste lisible sans JavaScript avancé.

## 5. Règles de sécurité

- La page projection reste côté formateur, protégée par authentification.
- Aucun secret n'est affiché.
- Le QR code ne contient que l'URL élèves locale.
- Aucun lien admin, export ou dashboard n'est exposé côté étudiant.

## 6. Règles offline

- Aucun CDN
- Aucun build frontend
- JavaScript et CSS locaux uniquement

## 7. Limites

- L'accès téléphone dépend toujours du Wi-Fi, du pare-feu, du portproxy et de
  la configuration `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`.
- Si l'IP LAN n'est pas configurée ou si elle est obsolète, le cockpit affiche
  un message prudent au lieu d'un faux lien sûr.
- Un vrai test téléphone reste nécessaire avant usage terrain.

## 8. Prochaines étapes

- F038 : médiathèque documents
- F039 : vidéo locale
