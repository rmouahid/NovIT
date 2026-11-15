# Rétrospective NovIT v1

Ce bilan porte sur les livrables v1.0.0 et v1.1.0 décrits dans le
[CHANGELOG](../CHANGELOG.md). Il s'appuie sur le code et les documents du
dépôt ; il ne prétend pas restituer des entretiens ni des retours utilisateur
qui n'ont pas été collectés.

## Ce qui a fonctionné

- **Un contrat commun par source.** `BaseScraper` et `Article` isolent les
  particularités des API et flux RSS. La configuration YAML et le
  [système de plugins](PLUGINS.md) permettent d'étendre la collecte sans
  réécrire les outils MCP.
- **La séparation collecte, stockage et présentation.** SQLite/FTS5 permet
  de rechercher des mots entiers et de servir le contenu déjà collecté.
  Le mode dégradé affiche l'âge des données au lieu de présenter un cache
  ancien comme une veille fraîche.
- **Une validation au niveau du protocole.** Les tests avec le client SDK
  sur stdio complètent les tests unitaires. Les réponses structurées et les
  schémas de sortie de v1.1.0 rendent les résultats exploitables par des
  clients qui ne se limitent pas au Markdown.
- **Des décisions documentées.** Les ADR explicitent les choix de transport,
  de cache, de base et d'authentification. Les guides de contribution et de
  publication rendent leur maintenance reproductible.

## Ce qui aurait pu être mieux fait

- **Tester les garanties transversales par leur effet.** Le limiteur de
  débit existait avant d'être appelé par toutes les sources. La correction
  v1.1.0 centralise les requêtes dans `scrapers/http.py`. Un test qui
  vérifie seulement l'objet limiteur n'établit pas la politesse du système.
- **Valider plus tôt dans un vrai client.** Les corrections de dates UTC,
  de préférences attendues à tort avec `await` et d'étiquettes GitHub
  Trending montrent l'utilité des scénarios de session complets. Les
  captures du client de bureau restent un livrable distinct de la démo SDK.
- **Distinguer les livrables de leur déploiement.** Un workflow de
  publication ne prouve pas qu'un paquet est disponible sur PyPI ; un
  manifeste ne prouve pas une inscription au registre MCP. Les issues de
  publication doivent conserver un lien vérifiable vers le résultat.
- **Séparer mesures et protocole d'évaluation.** `EVAL_RESULTS.md` décrit
  les critères mais sa grille manuelle reste à compléter. Les mesures de
  collecte de `PERFORMANCE.md` ne prouvent pas à elles seules la pertinence
  des articles pour chaque profil.
- **Utiliser un corpus représentatif des tendances.** Les titres CVE
  répètent des termes de gabarit. Le classement doit filtrer ce bruit et
  limiter le poids d'une seule source, avec une régression sur un corpus
  figé plutôt qu'une vérification visuelle des premiers mots.

## Décisions à réévaluer pour la v2

| Décision | Signal qui justifierait un changement | Vérification attendue |
|---|---|---|
| SQLite et rétention courte | contention ou besoin d'historique plus long | charge multi-utilisateurs, croissance disque, temps de recherche |
| Cache mémoire par processus | plusieurs instances divergent | cohérence et isolation par utilisateur sur deux instances |
| Scoring et profils prédéfinis | faible pertinence mesurée par profil | jeu annoté, scores par domaine et analyse des erreurs |
| Extraction lexicale des tendances | sujets encore dominés par le bruit ou les synonymes | comparaison sur corpus figé, coût et explicabilité |
| Jetons HTTP statiques | rotation ou délégation trop coûteuses | tests de révocation, journalisation et isolation des sessions |
| Dépendance au SDK MCP | évolution du protocole ou des clients | matrice SDK minimal/récent et scénarios stdio/HTTP |

## Priorités proposées

1. Terminer les preuves de publication, les captures du client et
   l'évaluation manuelle avant de communiquer des garanties supplémentaires.
2. Conserver une régression par incident réel et tester les parcours
   critiques avec plusieurs utilisateurs et des sources indisponibles.
3. Mesurer avant de remplacer SQLite, le cache ou le scoring : une v2 ne
   nécessite pas à elle seule davantage d'infrastructure.
