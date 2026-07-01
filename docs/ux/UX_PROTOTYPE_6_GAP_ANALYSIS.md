# UX Prototype 6 Gap Analysis

## But

Comparer la cible Prototype 6 et l’application réelle, sans confondre :

- ce qui existe déjà ;
- ce qui a été amorcé ;
- ce qui reste à intégrer ;
- ce qu’il ne faut surtout pas intégrer aveuglément.

## Résumé exécutif

Prototype 6 a déjà influencé :

- l’accueil ;
- le shell global ;
- les cartes ;
- le cockpit ;
- la projection ;
- la médiathèque publique ;
- certains états et composants.

Mais il n’a pas encore été traduit en blueprint UX global unifié. C’est
précisément l’objet de F045A.

## Ce qui est déjà proche du Prototype 6

### 1. Accueil

- séparation étudiant/formateur claire ;
- hero plus structuré ;
- cartes d’entrée plus assumées.

### 2. Shell et design system local

- header partagé ;
- badges ;
- cartes ;
- breadcrumbs ;
- boutons ;
- empty states ;
- responsive raisonnable.

### 3. Cockpit formateur

- vue hub ;
- stats ;
- accès élèves ;
- projection ;
- outils réseau ;
- supports.

### 4. Projection / QR

- vraie page dédiée ;
- URL élève mise en avant ;
- QR local ;
- fullscreen.

### 5. Médiathèque

- catalogue public ;
- détail support ;
- vidéo locale ;
- upload formateur minimal.

## Ce qui reste partiel

### 1. Blueprint UX global

- pas de documentation consolidée avant F045A ;
- plusieurs zones ont évolué sans matrice d’actions unique.

### 2. Cohérence de wording

- `voir`, `consulter`, `commencer`, `ouvrir`, `dashboard`, `cockpit`
  coexistent encore sans système documentaire unique.

### 3. Réseau

- trois pages distinctes existent :
  - réseau ;
  - contrôle LAN ;
  - configuration ;
- la séparation est techniquement bonne, mais pas encore UX-documentée de bout
  en bout.

### 4. Dashboards modules

- solides fonctionnellement ;
- moins ambitieux visuellement que la cible Prototype 6 ;
- encore principalement “tables + stats”.

### 5. Admin avancé

- utile et assumé ;
- peu intégré à une doctrine UX “escalade expert”.

## Ce qui n’existe pas encore dans l’application réelle

- hub UX complet des matières / ressources scolaires comme surface publique
  autonome ;
- orchestration UI totalement homogène de tous les écrans selon un langage
  design unique ;
- scénarios avancés de gestion contenus au-delà de l’upload minimal ;
- système de feedback plus narratif sur certaines actions staff.

## Ce qu’il ne faut pas copier du Prototype 6

- dépendance CDN ;
- architecture frontend lourde ;
- composants qui masqueraient les contraintes réseau réelles ;
- parcours “trop parfaits” qui feraient oublier la dépendance LAN locale ;
- promesses pédagogiques ou navigation futures non encore implémentées.

## Écarts principaux à traiter en priorité

1. documenter la navigation et les actions avant toute nouvelle refonte visuelle ;
2. clarifier l’architecture UX du triptyque réseau / contrôle LAN / configuration ;
3. harmoniser les états module ouvert / fermé / indisponible ;
4. mieux formaliser la médiathèque comme système UX complet ;
5. préparer un lot spécifique sur dashboards modules et exports.

## Écarts faibles ou acceptables

- sobriété visuelle de certaines tables ;
- usage d’admin Django pour fonctions avancées ;
- rendu très opérationnel de `network-control`.

## Conclusion

Prototype 6 est déjà une cible partiellement intégrée. Le plus grand manque
avant les prochaines PR UI n’est plus un manque de composants, mais un manque
de doctrine UX documentée et traçable. F045A comble ce point.
