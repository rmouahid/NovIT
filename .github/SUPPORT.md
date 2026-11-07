# Obtenir de l'aide sur NovIT

## Où poser quoi

| Besoin | Canal |
|---|---|
| Question d'installation ou d'usage | [Discussions → Q&A](https://github.com/rmouahid/NovIT/discussions/categories/q-a) |
| Idée encore floue, retour d'expérience | [Discussions → Ideas](https://github.com/rmouahid/NovIT/discussions/categories/ideas) |
| Bug reproductible | [Issue « Signalement de bug »](https://github.com/rmouahid/NovIT/issues/new?template=bug_report.yml) |
| Fonctionnalité ou nouvelle source | [Issue « Fonctionnalité »](https://github.com/rmouahid/NovIT/issues/new/choose) |
| Faille de sécurité | **Jamais en public** : voir [SECURITY.md](../SECURITY.md) |
| Annonces (releases, changements importants) | [Discussions → Announcements](https://github.com/rmouahid/NovIT/discussions/categories/announcements) |

Avant d'ouvrir une issue, vérifier la [documentation](../docs/) et les
[issues existantes](https://github.com/rmouahid/NovIT/issues?q=is%3Aissue).
Pour un bug, joindre la version (`novit --version` ou le fichier `VERSION`), le
client MCP utilisé et la sortie de `novit_health`.

## Délais de réponse

NovIT est maintenu par une seule personne sur son temps libre. Ces délais sont
des engagements de **première réponse** (accusé de réception et qualification),
pas de correction :

| Type | Exemple | Première réponse | Objectif de correction |
|---|---|---|---|
| Sécurité | fuite de jeton, exécution de code | 48 h | correctif ou contournement sous 7 jours |
| Bug critique (`P0`) | le serveur ne démarre plus, aucun outil ne répond | 48 h | prochaine version corrective |
| Bug (`P1`) | un outil renvoie un résultat faux | 7 jours | version mineure suivante |
| Fonctionnalité, question | | 14 jours | selon la roadmap |

## Triage des issues entrantes

Chaque nouvelle issue reçoit automatiquement le label `a-trier`. Une fois par
semaine (et sous 48 h pour ce qui ressemble à un `P0`), le mainteneur :

1. **Reproduit ou qualifie** : demande les informations manquantes si besoin
   (sans réponse sous 14 jours, l'issue est fermée et peut être rouverte).
2. **Classe** : type (`bug`, `feature`, `doc`, `chore`) et priorité :
   - `P0` : service cassé pour tous, ou faille de sécurité ;
   - `P1` : fonctionnalité dégradée, contournement possible ;
   - `P2` : amélioration, confort.
3. **Rattache** à un milestone de la [roadmap](../docs/ROADMAP.md), ou ferme
   avec une explication (`duplicate`, `wontfix`, `invalid`).
4. **Retire** `a-trier`. Les issues simples reçoivent `good first issue`.

Une question posée en issue est déplacée vers les Discussions ; une discussion
qui révèle un bug devient une issue.
