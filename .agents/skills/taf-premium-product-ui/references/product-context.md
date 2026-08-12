# Contexte produit TAf

TAf Local Forms est une application Django locale utilisée par un formateur
pendant une séance au lycée. Les élèves utilisent un téléphone connecté au
même Wi-Fi ou hotspot et ouvrent un questionnaire via l’adresse LAN du poste.

## Priorités

1. Comprendre quoi faire maintenant.
2. Conserver des données réelles et vérifiables.
3. Rester utilisable lorsque le réseau, le helper ou l’environnement Windows
   n’est pas confirmé.
4. Séparer clairement les parcours étudiant et formateur.
5. Préserver les routes, l’authentification, les sauvegardes et l’anti-doublon.

## Contextes

- étudiant : téléphone, petit écran, texte simple, une décision à la fois ;
- formateur : poste local, pression temporelle, Cockpit et opérations LAN ;
- administration : fonctions avancées séparées et clairement signalées.

Les nombres du dashboard doivent distinguer élèves uniques, participants,
soumissions, réponses et scores. Une adresse IP ou un état réseau non prouvé
doit rester explicitement non confirmé.
