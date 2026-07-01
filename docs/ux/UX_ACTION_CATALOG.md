# UX Action Catalog

## Méthode

Chaque action ci-dessous suit le même format :

- Action ID
- Rôle
- Page
- Objectif utilisateur
- Déclencheur
- Préconditions
- Bouton/lien visible
- Route Django
- Méthode HTTP
- Résultat attendu
- État succès
- État erreur
- Message utilisateur
- Protection login
- CSRF
- Test attendu
- Écart Prototype 6
- Priorité

## Couverture

Nombre approximatif d'actions documentées : 51.

Répartition :

- étudiant : 19
- formateur : 26
- staff/opérations : 6

---

## A. Accueil et navigation primaire

### UX-A001

- Action ID : `UX-A001`
- Rôle : étudiant, formateur
- Page : accueil
- Objectif utilisateur : choisir son espace
- Déclencheur : arrivée sur `/`
- Préconditions : application accessible
- Bouton/lien visible : `Entrer côté étudiant`
- Route Django : `/modules/`
- Méthode HTTP : `GET`
- Résultat attendu : ouverture du catalogue modules
- État succès : page modules affichée
- État erreur : indisponibilité serveur
- Message utilisateur : aucun message spécifique
- Protection login : non
- CSRF : non
- Test attendu : home contient lien vers `student_modules`
- Écart Prototype 6 : conforme
- Priorité : P0

### UX-A002

- Action ID : `UX-A002`
- Rôle : formateur
- Page : accueil
- Objectif utilisateur : entrer dans le cockpit
- Déclencheur : clic CTA formateur
- Préconditions : route dashboard disponible
- Bouton/lien visible : `Ouvrir le cockpit formateur`
- Route Django : `/dashboard/`
- Méthode HTTP : `GET`
- Résultat attendu : redirection login si non connecté, cockpit sinon
- État succès : cockpit affiché
- État erreur : redirection login
- Message utilisateur : écran login admin Django
- Protection login : oui
- CSRF : non
- Test attendu : home contient lien vers `dashboard_home`
- Écart Prototype 6 : conforme
- Priorité : P0

### UX-A003

- Action ID : `UX-A003`
- Rôle : étudiant
- Page : navigation étudiante
- Objectif utilisateur : ouvrir les supports publics
- Déclencheur : clic `Supports`
- Préconditions : au moins route publique accessible
- Bouton/lien visible : `Supports`
- Route Django : `/supports/`
- Méthode HTTP : `GET`
- Résultat attendu : catalogue public
- État succès : filtres et cartes supports visibles
- État erreur : catalogue vide
- Message utilisateur : `Aucun support publié`
- Protection login : non
- CSRF : non
- Test attendu : navigation étudiante contient `/supports/`
- Écart Prototype 6 : partiel, moins riche
- Priorité : P1

### UX-A004

- Action ID : `UX-A004`
- Rôle : étudiant
- Page : navigation étudiante
- Objectif utilisateur : revenir à l’accueil
- Déclencheur : clic `Accueil`
- Préconditions : aucune
- Bouton/lien visible : `Accueil`
- Route Django : `/`
- Méthode HTTP : `GET`
- Résultat attendu : retour sas d'entrée
- État succès : accueil affiché
- État erreur : aucune spécifique
- Message utilisateur : aucun
- Protection login : non
- CSRF : non
- Test attendu : nav student contient lien `/`
- Écart Prototype 6 : conforme
- Priorité : P1

## B. Parcours modules étudiant

### UX-M001

- Action ID : `UX-M001`
- Rôle : étudiant
- Page : `/modules/`
- Objectif utilisateur : consulter un module ouvert
- Déclencheur : clic `Voir le module`
- Préconditions : session active
- Bouton/lien visible : `Voir le module`
- Route Django : `/modules/module-X/`
- Méthode HTTP : `GET`
- Résultat attendu : détail module
- État succès : bloc pédagogique + CTA questionnaire
- État erreur : module indisponible
- Message utilisateur : `Aucune session active`
- Protection login : non
- CSRF : non
- Test attendu : student modules affiche `Voir le module`
- Écart Prototype 6 : conforme
- Priorité : P0

### UX-M002

- Action ID : `UX-M002`
- Rôle : étudiant
- Page : détail module
- Objectif utilisateur : commencer le questionnaire
- Déclencheur : clic `Commencer le questionnaire`
- Préconditions : session active, réponses ouvertes
- Bouton/lien visible : `Commencer le questionnaire`
- Route Django : `/module-X/`
- Méthode HTTP : `GET`
- Résultat attendu : questionnaire module
- État succès : formulaire complet affiché
- État erreur : session absente
- Message utilisateur : page indisponible
- Protection login : non
- CSRF : non
- Test attendu : detail module contient CTA
- Écart Prototype 6 : conforme
- Priorité : P0

### UX-M003

- Action ID : `UX-M003`
- Rôle : étudiant
- Page : détail module
- Objectif utilisateur : consulter un questionnaire fermé
- Déclencheur : clic `Consulter le questionnaire`
- Préconditions : session active, réponses fermées
- Bouton/lien visible : `Consulter le questionnaire`
- Route Django : `/module-X/`
- Méthode HTTP : `GET`
- Résultat attendu : formulaire lisible sans envoi
- État succès : alerte fermeture + bouton submit absent
- État erreur : aucune session active
- Message utilisateur : `Les réponses sont fermées`
- Protection login : non
- CSRF : non
- Test attendu : modules fermés restent consultables
- Écart Prototype 6 : important à maintenir
- Priorité : P0

### UX-M004

- Action ID : `UX-M004`
- Rôle : étudiant
- Page : questionnaire module
- Objectif utilisateur : envoyer sa réponse
- Déclencheur : clic `Envoyer`
- Préconditions : session active, réponses ouvertes, formulaire valide
- Bouton/lien visible : `Envoyer`
- Route Django : `/module-X/`
- Méthode HTTP : `POST`
- Résultat attendu : création réponse + redirect succès
- État succès : page merci
- État erreur : champs invalides ou doublon
- Message utilisateur : validation ou message doublon
- Protection login : non
- CSRF : oui
- Test attendu : POST valide redirige succès
- Écart Prototype 6 : conforme mais texte encore variable selon modules
- Priorité : P0

### UX-M005

- Action ID : `UX-M005`
- Rôle : étudiant
- Page : questionnaire module
- Objectif utilisateur : corriger un identifiant invalide
- Déclencheur : validation serveur
- Préconditions : `school_id_number` incorrect
- Bouton/lien visible : champ numéro
- Route Django : `/module-X/`
- Méthode HTTP : `POST`
- Résultat attendu : formulaire réaffiché avec erreur
- État succès : erreur explicite visible
- État erreur : message ambigu
- Message utilisateur : `Entre exactement 2 chiffres`
- Protection login : non
- CSRF : oui
- Test attendu : payload invalide affiche l’erreur
- Écart Prototype 6 : doit rester ultra lisible mobile
- Priorité : P0

### UX-M006

- Action ID : `UX-M006`
- Rôle : étudiant
- Page : questionnaire module
- Objectif utilisateur : comprendre le refus de doublon
- Déclencheur : seconde soumission même numéro / session
- Préconditions : réponse déjà existante
- Bouton/lien visible : champ numéro
- Route Django : `/module-X/`
- Méthode HTTP : `POST`
- Résultat attendu : refus sans création
- État succès : message doublon clair
- État erreur : message trop technique
- Message utilisateur : `Une réponse existe déjà pour ce numéro`
- Protection login : non
- CSRF : oui
- Test attendu : doublon bloqué
- Écart Prototype 6 : état critique à expliciter davantage
- Priorité : P0

### UX-M007

- Action ID : `UX-M007`
- Rôle : étudiant
- Page : success module
- Objectif utilisateur : confirmer l’enregistrement
- Déclencheur : redirect après POST valide
- Préconditions : id de dernière soumission en session
- Bouton/lien visible : aucun déclencheur direct
- Route Django : `/module-X/success/<id>/`
- Méthode HTTP : `GET`
- Résultat attendu : page merci
- État succès : confirmation positive
- État erreur : accès direct interdit
- Message utilisateur : `Merci. Ta réponse a bien été enregistrée.`
- Protection login : non
- CSRF : non
- Test attendu : accès direct sans session redirige vers le questionnaire
- Écart Prototype 6 : conforme
- Priorité : P1

### UX-M008

- Action ID : `UX-M008`
- Rôle : étudiant
- Page : unavailable module
- Objectif utilisateur : comprendre que la séance n'est pas ouverte
- Déclencheur : ouverture d’un questionnaire sans session active
- Préconditions : aucune session active
- Bouton/lien visible : accès direct ou CTA
- Route Django : `/module-X/`
- Méthode HTTP : `GET`
- Résultat attendu : page 503 dédiée
- État succès : message simple
- État erreur : message trop technique
- Message utilisateur : `Le formulaire n'est pas disponible maintenant.`
- Protection login : non
- CSRF : non
- Test attendu : route retourne 503
- Écart Prototype 6 : état à harmoniser sur tous les modules
- Priorité : P0

## C. Supports publics et médias

### UX-S001

- Action ID : `UX-S001`
- Rôle : étudiant
- Page : catalogue supports
- Objectif utilisateur : filtrer par matière
- Déclencheur : choix dans select puis `Filtrer`
- Préconditions : matières publiées existantes
- Bouton/lien visible : `Filtrer`
- Route Django : `/supports/?subject=<slug>`
- Méthode HTTP : `GET`
- Résultat attendu : liste réduite
- État succès : seuls les supports correspondants restent visibles
- État erreur : aucun résultat
- Message utilisateur : `Aucun support publié`
- Protection login : non
- CSRF : non
- Test attendu : filtre sujet
- Écart Prototype 6 : conforme mais sobre
- Priorité : P1

### UX-S002

- Action ID : `UX-S002`
- Rôle : étudiant
- Page : catalogue supports
- Objectif utilisateur : filtrer par niveau
- Déclencheur : select niveau
- Préconditions : matières avec niveau
- Bouton/lien visible : `Filtrer`
- Route Django : `/supports/?level=<value>`
- Méthode HTTP : `GET`
- Résultat attendu : ressources du niveau
- État succès : liste cohérente
- État erreur : aucun résultat
- Message utilisateur : empty state
- Protection login : non
- CSRF : non
- Test attendu : filtre niveau
- Écart Prototype 6 : conforme
- Priorité : P2

### UX-S003

- Action ID : `UX-S003`
- Rôle : étudiant
- Page : catalogue supports
- Objectif utilisateur : filtrer par module
- Déclencheur : select module
- Préconditions : module number présent
- Bouton/lien visible : `Filtrer`
- Route Django : `/supports/?module=<n>`
- Méthode HTTP : `GET`
- Résultat attendu : ressources ciblées
- État succès : liste réduite
- État erreur : aucun résultat
- Message utilisateur : empty state
- Protection login : non
- CSRF : non
- Test attendu : filtre module
- Écart Prototype 6 : conforme
- Priorité : P2

### UX-S004

- Action ID : `UX-S004`
- Rôle : étudiant
- Page : catalogue supports
- Objectif utilisateur : ouvrir le détail d’un support
- Déclencheur : clic titre ou `Voir le détail`
- Préconditions : support publié
- Bouton/lien visible : `Voir le détail`
- Route Django : `/supports/<slug>/`
- Méthode HTTP : `GET`
- Résultat attendu : détail support
- État succès : métadonnées et actions visibles
- État erreur : brouillon ou slug absent
- Message utilisateur : 404
- Protection login : non
- CSRF : non
- Test attendu : détail publié 200, brouillon 404
- Écart Prototype 6 : conforme
- Priorité : P1

### UX-S005

- Action ID : `UX-S005`
- Rôle : étudiant
- Page : détail support
- Objectif utilisateur : télécharger le fichier
- Déclencheur : clic `Télécharger le support`
- Préconditions : fichier disponible, support publié
- Bouton/lien visible : `Télécharger`
- Route Django : `/supports/<slug>/download/`
- Méthode HTTP : `GET`
- Résultat attendu : download navigateur
- État succès : fichier servi
- État erreur : support draft ou fichier absent
- Message utilisateur : 404 implicite
- Protection login : non
- CSRF : non
- Test attendu : download publié 200
- Écart Prototype 6 : conforme
- Priorité : P1

### UX-S006

- Action ID : `UX-S006`
- Rôle : étudiant
- Page : détail support vidéo
- Objectif utilisateur : regarder une vidéo locale
- Déclencheur : clic `Regarder la vidéo`
- Préconditions : support publié + type vidéo
- Bouton/lien visible : `Regarder la vidéo`
- Route Django : `/supports/<slug>/watch/`
- Méthode HTTP : `GET`
- Résultat attendu : page player HTML5
- État succès : `<video controls preload="metadata">`
- État erreur : route non vidéo ou brouillon
- Message utilisateur : 404 ou fallback download dans player
- Protection login : non
- CSRF : non
- Test attendu : watch vidéo 200 ; doc ou brouillon 404
- Écart Prototype 6 : conforme, volontairement minimal
- Priorité : P1

## D. Cockpit formateur

### UX-D001

- Action ID : `UX-D001`
- Rôle : formateur
- Page : cockpit
- Objectif utilisateur : accéder au hub de séance
- Déclencheur : ouverture `/dashboard/`
- Préconditions : login valide
- Bouton/lien visible : navigation `Cockpit`
- Route Django : `/dashboard/`
- Méthode HTTP : `GET`
- Résultat attendu : cockpit avec sections
- État succès : overview, accès, modules, présence, exports, outils
- État erreur : redirect login
- Message utilisateur : login admin si non connecté
- Protection login : oui
- CSRF : non
- Test attendu : dashboard home 302 sans login, 200 avec login
- Écart Prototype 6 : conforme mais dense
- Priorité : P0

### UX-D002

- Action ID : `UX-D002`
- Rôle : formateur
- Page : cockpit
- Objectif utilisateur : copier l’URL élèves
- Déclencheur : bouton `Copier l'URL élèves`
- Préconditions : `student_access_ready`
- Bouton/lien visible : `Copier l'URL élèves`
- Route Django : `/dashboard/`
- Méthode HTTP : client-side
- Résultat attendu : copie presse-papiers
- État succès : message aria-live
- État erreur : bouton désactivé si pas d’URL
- Message utilisateur : feedback de copie
- Protection login : oui
- CSRF : non
- Test attendu : présence de la zone de copie
- Écart Prototype 6 : conforme
- Priorité : P1

### UX-D003

- Action ID : `UX-D003`
- Rôle : formateur
- Page : cockpit modules
- Objectif utilisateur : ouvrir un dashboard module
- Déclencheur : clic `Dashboard`
- Préconditions : session active du module
- Bouton/lien visible : `Dashboard`
- Route Django : `/dashboard/module-X/`
- Méthode HTTP : `GET`
- Résultat attendu : vue module
- État succès : stats + filtre + table réponses
- État erreur : login absent
- Message utilisateur : redirect login
- Protection login : oui
- CSRF : non
- Test attendu : dashboard module protégé
- Écart Prototype 6 : conforme
- Priorité : P0

### UX-D004

- Action ID : `UX-D004`
- Rôle : staff formateur
- Page : cockpit modules
- Objectif utilisateur : ouvrir ou fermer les réponses
- Déclencheur : clic toggle
- Préconditions : session active + rôle staff
- Bouton/lien visible : `Fermer les réponses` / `Ouvrir les réponses`
- Route Django : `/dashboard/modules/<module_code>/toggle-responses/`
- Méthode HTTP : `POST`
- Résultat attendu : changement de statut session
- État succès : retour cockpit avec nouveau libellé
- État erreur : refus permission
- Message utilisateur : pas de message riche actuellement
- Protection login : oui + staff
- CSRF : oui
- Test attendu : accès staff seulement
- Écart Prototype 6 : état d’action à clarifier visuellement
- Priorité : P0

### UX-D005

- Action ID : `UX-D005`
- Rôle : formateur
- Page : cockpit exports
- Objectif utilisateur : télécharger un CSV module
- Déclencheur : clic carte export
- Préconditions : login valide
- Bouton/lien visible : `Export Module X`
- Route Django : `/dashboard/export/module-X.csv`
- Méthode HTTP : `GET`
- Résultat attendu : téléchargement CSV
- État succès : fichier servi
- État erreur : login absent
- Message utilisateur : aucune interface intermédiaire
- Protection login : oui
- CSRF : non
- Test attendu : export protégé puis 200 avec login
- Écart Prototype 6 : conforme
- Priorité : P1

## E. Réseau, configuration et contrôle LAN

### UX-N001

- Action ID : `UX-N001`
- Rôle : formateur
- Page : accès réseau
- Objectif utilisateur : voir l’adresse recommandée à donner aux élèves
- Déclencheur : ouverture page réseau
- Préconditions : login
- Bouton/lien visible : `Réseau`
- Route Django : `/dashboard/network/`
- Méthode HTTP : `GET`
- Résultat attendu : URL recommandée + diagnostics
- État succès : IP et URLs visibles
- État erreur : IP non configurée ou obsolète
- Message utilisateur : warning explicite
- Protection login : oui
- CSRF : non
- Test attendu : dashboard network 200 avec contenu réseau
- Écart Prototype 6 : plus technique que la cible
- Priorité : P0

### UX-N002

- Action ID : `UX-N002`
- Rôle : staff formateur
- Page : configuration réseau
- Objectif utilisateur : utiliser l’adresse LAN actuelle
- Déclencheur : bouton `Utiliser l'adresse actuelle`
- Préconditions : accès via LAN détecté, rôle staff
- Bouton/lien visible : `Utiliser l'adresse actuelle`
- Route Django : `/dashboard/settings/use-current-address/`
- Méthode HTTP : `POST`
- Résultat attendu : mise à jour paramètres réseau documentés
- État succès : message `Valeur enregistrée`
- État erreur : permission ou validation
- Message utilisateur : confirmation succès / erreur
- Protection login : oui + staff
- CSRF : oui
- Test attendu : route protégée + message succès
- Écart Prototype 6 : non couvert directement
- Priorité : P1

### UX-N003

- Action ID : `UX-N003`
- Rôle : staff formateur
- Page : configuration réseau
- Objectif utilisateur : modifier un paramètre réseau éditable
- Déclencheur : formulaire par clé
- Préconditions : rôle staff
- Bouton/lien visible : `Enregistrer`
- Route Django : `/dashboard/settings/`
- Méthode HTTP : `POST`
- Résultat attendu : valeur persistée
- État succès : message de sauvegarde
- État erreur : valeur interdite ou format invalide
- Message utilisateur : `Valeur enregistrée` ou erreur
- Protection login : oui + staff
- CSRF : oui
- Test attendu : valeurs réseau validées
- Écart Prototype 6 : plus back-office
- Priorité : P1

### UX-N004

- Action ID : `UX-N004`
- Rôle : staff formateur
- Page : contrôle LAN
- Objectif utilisateur : synchroniser l’accès LAN
- Déclencheur : bouton `Configurer et rendre accessible`
- Préconditions : localhost, helper disponible, rôle staff
- Bouton/lien visible : `Configurer et rendre accessible`
- Route Django : `/dashboard/network-control/` + helper local `127.0.0.1:8019`
- Méthode HTTP : client-side fetch
- Résultat attendu : portproxy + pare-feu + sync
- État succès : résultat JSON + état global mis à jour
- État erreur : helper absent / timeout / hors localhost
- Message utilisateur : alert succès ou erreur helper
- Protection login : oui + staff
- CSRF : non côté helper fetch
- Test attendu : page contient boutons et scripts helper
- Écart Prototype 6 : plus opérationnel que visuel
- Priorité : P0

### UX-N005

- Action ID : `UX-N005`
- Rôle : staff formateur
- Page : contrôle LAN
- Objectif utilisateur : tester l’URL élèves
- Déclencheur : bouton `Tester l'URL élèves`
- Préconditions : helper disponible
- Bouton/lien visible : `Tester l'URL élèves`
- Route Django : page contrôle LAN + helper local
- Méthode HTTP : client-side fetch
- Résultat attendu : statut d’accessibilité LAN
- État succès : step 7 mis à jour
- État erreur : timeout ou helper absent
- Message utilisateur : carte statut + message helper
- Protection login : oui + staff
- CSRF : non côté helper fetch
- Test attendu : page contient action test
- Écart Prototype 6 : non documenté dans prototype
- Priorité : P0

### UX-N006

- Action ID : `UX-N006`
- Rôle : staff formateur
- Page : contrôle LAN
- Objectif utilisateur : redémarrer l’application
- Déclencheur : bouton `Redémarrer l'application`
- Préconditions : helper disponible
- Bouton/lien visible : `Redémarrer l'application`
- Route Django : page contrôle LAN + helper local
- Méthode HTTP : client-side fetch
- Résultat attendu : restart web
- État succès : message helper
- État erreur : helper absent / Docker indisponible
- Message utilisateur : résultat JSON et message d’erreur si besoin
- Protection login : oui + staff
- CSRF : non côté helper fetch
- Test attendu : page contient action restart
- Écart Prototype 6 : non couvert
- Priorité : P2

### UX-N007

- Action ID : `UX-N007`
- Rôle : staff formateur
- Page : contrôle LAN
- Objectif utilisateur : désactiver l’accès LAN
- Déclencheur : bouton `Désactiver l'accès LAN`
- Préconditions : helper disponible, confirmation navigateur
- Bouton/lien visible : `Désactiver l'accès LAN`
- Route Django : page contrôle LAN + helper local
- Méthode HTTP : client-side fetch
- Résultat attendu : suppression portproxy et règle pare-feu
- État succès : statut dégradé propre
- État erreur : helper absent
- Message utilisateur : confirmation puis résultat
- Protection login : oui + staff
- CSRF : non côté helper fetch
- Test attendu : présence `confirm(`
- Écart Prototype 6 : non couvert
- Priorité : P2

## F. Supports dashboard et upload

### UX-L001

- Action ID : `UX-L001`
- Rôle : formateur
- Page : dashboard supports
- Objectif utilisateur : voir brouillons et publiés
- Déclencheur : ouverture page
- Préconditions : login
- Bouton/lien visible : `Supports`
- Route Django : `/dashboard/supports/`
- Méthode HTTP : `GET`
- Résultat attendu : tableau des ressources
- État succès : badges publié/brouillon, liens d’action
- État erreur : redirect login
- Message utilisateur : empty state si rien
- Protection login : oui
- CSRF : non
- Test attendu : dashboard supports protégé puis visible
- Écart Prototype 6 : plus minimal que la cible
- Priorité : P1

### UX-L002

- Action ID : `UX-L002`
- Rôle : formateur
- Page : dashboard supports
- Objectif utilisateur : ouvrir le formulaire d’upload
- Déclencheur : clic `Ajouter un support`
- Préconditions : login
- Bouton/lien visible : `Ajouter un support`
- Route Django : `/dashboard/supports/upload/`
- Méthode HTTP : `GET`
- Résultat attendu : formulaire d’upload
- État succès : form affiché
- État erreur : redirect login
- Message utilisateur : aucun
- Protection login : oui
- CSRF : non
- Test attendu : lien visible dans dashboard supports
- Écart Prototype 6 : conforme mais encore simple
- Priorité : P1

### UX-L003

- Action ID : `UX-L003`
- Rôle : formateur
- Page : upload support
- Objectif utilisateur : créer un support brouillon
- Déclencheur : submit sans cocher publication
- Préconditions : login, fichier valide
- Bouton/lien visible : `Enregistrer le support`
- Route Django : `/dashboard/supports/upload/`
- Méthode HTTP : `POST`
- Résultat attendu : création d’un `LearningResource`
- État succès : redirect liste supports
- État erreur : validation
- Message utilisateur : message succès Django
- Protection login : oui
- CSRF : oui
- Test attendu : création draft ne sort pas côté public
- Écart Prototype 6 : conforme
- Priorité : P1

### UX-L004

- Action ID : `UX-L004`
- Rôle : formateur
- Page : upload support
- Objectif utilisateur : publier immédiatement un support
- Déclencheur : submit avec `Publier`
- Préconditions : login, fichier valide
- Bouton/lien visible : checkbox publication + submit
- Route Django : `/dashboard/supports/upload/`
- Méthode HTTP : `POST`
- Résultat attendu : support visible dans `/supports/`
- État succès : redirect + support public
- État erreur : validation
- Message utilisateur : message succès Django
- Protection login : oui
- CSRF : oui
- Test attendu : upload publié apparaît au catalogue
- Écart Prototype 6 : conforme
- Priorité : P1

### UX-L005

- Action ID : `UX-L005`
- Rôle : formateur
- Page : upload support
- Objectif utilisateur : relier matière et chapitre cohérents
- Déclencheur : saisie `subject` + `chapter`
- Préconditions : chapitre de la bonne matière
- Bouton/lien visible : sélecteurs matière/chapitre
- Route Django : `/dashboard/supports/upload/`
- Méthode HTTP : `POST`
- Résultat attendu : ressource correctement classée
- État succès : création support
- État erreur : chapitre d'une autre matière
- Message utilisateur : `Choisis un chapitre de la matière sélectionnée.`
- Protection login : oui
- CSRF : oui
- Test attendu : rejet incohérence sujet/chapitre
- Écart Prototype 6 : cible plus guidée souhaitable
- Priorité : P2

### UX-L006

- Action ID : `UX-L006`
- Rôle : formateur
- Page : upload support
- Objectif utilisateur : comprendre un format ou poids refusé
- Déclencheur : fichier invalide
- Préconditions : upload hors règles
- Bouton/lien visible : input fichier
- Route Django : `/dashboard/supports/upload/`
- Méthode HTTP : `POST`
- Résultat attendu : formulaire avec erreur
- État succès : erreur claire 20 MB / 80 MB / format
- État erreur : message imprécis
- Message utilisateur : format non autorisé ou taille max
- Protection login : oui
- CSRF : oui
- Test attendu : extensions et tailles rejetées
- Écart Prototype 6 : besoin d'aide UX plus visible
- Priorité : P1

## G. Sauvegarde et présence

### UX-B001

- Action ID : `UX-B001`
- Rôle : formateur
- Page : sauvegarde
- Objectif utilisateur : connaître la base active
- Déclencheur : ouverture `/dashboard/backup/`
- Préconditions : login
- Bouton/lien visible : `Sauvegarde`
- Route Django : `/dashboard/backup/`
- Méthode HTTP : `GET`
- Résultat attendu : moteur DB + commande backup
- État succès : infos visibles
- État erreur : redirect login
- Message utilisateur : avertissement anti-destruction
- Protection login : oui
- CSRF : non
- Test attendu : page contient `Sauvegarder les données`
- Écart Prototype 6 : plus opérationnel que graphique
- Priorité : P1

### UX-B002

- Action ID : `UX-B002`
- Rôle : formateur
- Page : cockpit présence
- Objectif utilisateur : suivre la présence active en direct
- Déclencheur : chargement cockpit
- Préconditions : login
- Bouton/lien visible : section `Présence`
- Route Django : `/dashboard/presence.json`
- Méthode HTTP : `GET`
- Résultat attendu : compteur périodique
- État succès : nombres mis à jour
- État erreur : aucun compteur exploitable
- Message utilisateur : pas de message spécifique
- Protection login : oui
- CSRF : non
- Test attendu : endpoint présence protégé puis 200
- Écart Prototype 6 : discret, pas encore mis en scène
- Priorité : P2

### UX-B003

- Action ID : `UX-B003`
- Rôle : étudiant, infrastructure locale
- Page : heartbeat de présence
- Objectif utilisateur : signaler silencieusement qu’un élève est encore présent sur un formulaire actif
- Déclencheur : chargement d’un formulaire module, intervalle 30s, passage en arrière-plan, fermeture de l’onglet
- Préconditions : formulaire module ouvert, `client_id` disponible en session, `csrfmiddlewaretoken` présent, session module active
- Bouton/lien visible : aucun, action technique invisible
- Route Django : `/presence/heartbeat/`
- Méthode HTTP : `POST`
- Résultat attendu : mise à jour ou création de présence côté serveur
- État succès : réponse JSON `ok`, présence visible ensuite dans le cockpit formateur
- État erreur : `400` payload incomplet, `404` session absente, polling interrompu ou réseau indisponible
- Message utilisateur : aucun message étudiant direct ; état traité comme télémétrie silencieuse
- Protection login : non
- CSRF : oui, via header `X-CSRFToken`
- Test attendu : `405` sur GET, `400/404/200` sur cas métier, intervalle 30s présent dans le partial
- Écart Prototype 6 : non visible dans la maquette, mais indispensable au suivi terrain
- Priorité : P0

## H. Projection salle

### UX-P001

- Action ID : `UX-P001`
- Rôle : formateur
- Page : projection
- Objectif utilisateur : afficher en grand l’URL élèves et le QR code pour la salle
- Déclencheur : ouverture de `/dashboard/projection/`
- Préconditions : login formateur, URL élèves calculable ou état LAN explicitement indisponible
- Bouton/lien visible : `Projection`, `Mode projection`, `Afficher la projection`
- Route Django : `/dashboard/projection/`
- Méthode HTTP : `GET`
- Résultat attendu : page projection avec URL, QR, étapes de connexion et retour cockpit
- État succès : URL visible, QR rendu, consignes courtes lisibles, warning si IP LAN obsolète
- État erreur : `URL LAN non configurée`, QR absent si JS ou bibliothèque QR indisponible
- Message utilisateur : `URL LAN non configurée` ou rappel de vérifier la page Réseau
- Protection login : oui
- CSRF : non
- Test attendu : redirection login sans session, rendu `Mode projection` avec session, absence des liens projection côté étudiant
- Écart Prototype 6 : aligné sur l’intention, avec un ton plus terrain
- Priorité : P0

### UX-P002

- Action ID : `UX-P002`
- Rôle : formateur
- Page : projection
- Objectif utilisateur : copier rapidement l’URL élèves depuis l’écran de projection
- Déclencheur : clic `Copier l'URL`
- Préconditions : URL élèves disponible ; JS local chargé
- Bouton/lien visible : `Copier l'URL`
- Route Django : `/dashboard/projection/`
- Méthode HTTP : `GET` + action JS locale
- Résultat attendu : URL copiée dans le presse-papiers
- État succès : feedback `URL copiée.`
- État erreur : URL absente ou copie indisponible sur le navigateur
- Message utilisateur : `URL LAN non configurée.` ou `Copie indisponible sur ce navigateur.`
- Protection login : oui
- CSRF : non
- Test attendu : présence du bouton, bouton désactivé si URL absente, JS partagé chargé
- Écart Prototype 6 : conforme, mais dépendance navigateur à expliciter
- Priorité : P0

### UX-P003

- Action ID : `UX-P003`
- Rôle : formateur
- Page : projection
- Objectif utilisateur : passer l’affichage en plein écran puis en sortir pendant la séance
- Déclencheur : clic `Plein écran`
- Préconditions : page projection ouverte ; API fullscreen disponible
- Bouton/lien visible : `Plein écran`
- Route Django : `/dashboard/projection/`
- Méthode HTTP : `GET` + action JS locale
- Résultat attendu : la carte projection occupe l’écran, puis revient à l’état normal à la sortie
- État succès : entrée ou sortie plein écran sans perte d’information
- État erreur : appareil ou navigateur sans support, ou refus d’activation
- Message utilisateur : `Plein écran indisponible sur cet appareil.` ou `Impossible d'activer le plein écran.`
- Protection login : oui
- CSRF : non
- Test attendu : présence du bouton `type="button"` et chargement du JS projection
- Écart Prototype 6 : conforme, avec contrainte navigateur réelle
- Priorité : P0

### UX-P004

- Action ID : `UX-P004`
- Rôle : formateur
- Page : projection
- Objectif utilisateur : revenir rapidement au cockpit formateur
- Déclencheur : clic `Retour cockpit`
- Préconditions : login formateur
- Bouton/lien visible : `Retour cockpit`
- Route Django : `/dashboard/`
- Méthode HTTP : `GET`
- Résultat attendu : retour au cockpit sans étape intermédiaire
- État succès : cockpit affiché
- État erreur : redirection login si session perdue
- Message utilisateur : aucun message spécifique
- Protection login : oui
- CSRF : non
- Test attendu : présence du lien retour vers `dashboard_home`
- Écart Prototype 6 : conforme
- Priorité : P1

## Résumé des priorités

- P0 : entrées principales, questionnaires, fermeture/ouverture réponses, URL
  élèves, contrôle LAN critique, projection, heartbeat technique
- P1 : supports, uploads, exports, backup, navigation de confort
- P2 : guidage avancé, poids média, présence cockpit plus lisible, opérations secondaires
