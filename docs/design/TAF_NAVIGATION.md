# TAF Navigation

## Objectif

F036 formalise une navigation simple et coherente pour les parcours etudiant et
formateur, en reutilisant les routes existantes et le design system local.

## Separation etudiant / formateur

- etudiant : `Accueil`, `Modules`, et un marqueur non cliquable
  `Supports bientot`
- formateur : `Cockpit`, `Modules`, `Exports`, `Reseau`, `Controle LAN`,
  `Configuration`, `Sauvegarde`, `Admin avance`

Cette separation evite d'exposer des fonctions de gestion cote public.

## Regles de securite

- aucun lien admin cote etudiant ;
- dashboard, exports et reseau restent proteges par authentification ;
- les diagnostics techniques restent reserves aux pages formateur ;
- aucune nouvelle route sensible n'est ajoutee.

## Breadcrumbs

- les breadcrumbs indiquent un parcours simple ;
- ils ne remplacent pas le menu principal ;
- ils ne cherchent pas a representer toute l'arborescence ;
- les liens de remontee vont seulement vers des racines deja sures :
  `Accueil`, `Modules`, `Cockpit`.

## Routes existantes utilisees

Routes publiques etudiant :

- `/`
- `/modules/`
- `/modules/module-2/` a `/modules/module-8/`
- `/module-2/` a `/module-8/`

Routes formateur protegees :

- `/dashboard/`
- `/dashboard/module-2/` a `/dashboard/module-8/`
- `/dashboard/export/module-2.csv` a `/dashboard/export/module-8.csv`
- `/dashboard/network/`
- `/dashboard/network-control/`
- `/dashboard/settings/`
- `/dashboard/backup/`
- `/admin/`

Routes absentes non inventees dans F036 :

- aucune route `/supports/` ou mediatheque n'existe encore ;
- aucun nouveau hub d'exports n'est ajoute ;
- la navigation `Exports` renvoie vers la section exports du cockpit existant.

## Prochaines etapes

- F037 : cockpit + QR local
- F038 : mediatheque
