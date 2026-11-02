# ADR-006 : Multi-utilisateurs — un jeton par utilisateur, état rangé par utilisateur

**Statut :** Acceptée
**Date :** 2026-11-02

## Contexte

Avec [ADR-005](0005-transport-http-authentification.md), une instance HTTP sert un seul
utilisateur : le profil, les domaines favoris et l'historique de session sont globaux au
processus, et deux clients connectés au même serveur se les partagent. #87 demande des profils
isolés, des préférences et un historique par utilisateur, sans fuite de l'un à l'autre.

Contraintes : ne rien changer à l'usage local (stdio, jeton unique), ne pas réécrire les
handlers, qui lisent les préférences via `prefs_store` et la session via `session_manager`,
et rester déployable sur l'instance unique décrite dans ADR-005 (SQLite sur un volume).

## Décision

1. **Identification** : `NOVIT_API_TOKENS="alice:jeton1,bob:jeton2"` associe un jeton à chaque
   utilisateur. `BearerTokenMiddleware` compare le jeton présenté à tous les jetons connus
   (comparaisons à temps constant, toutes effectuées) et dépose l'identifiant dans
   `request.state`. `NOVIT_API_TOKEN` reste accepté et vaut l'utilisateur `default`.
2. **Propagation** : `call_tool` lit l'utilisateur sur la requête HTTP
   (`ServerRequestContext.request`) et le place dans la `ContextVar` `current_user`
   (`novit/mcp/users.py`) pendant l'appel. En stdio, il vaut `default`.
3. **Isolation** : `PreferencesStore` lit `.novit_users/<utilisateur>.json` (inchangé pour
   `default` : `.novit_prefs.json`), `SessionManager` range les sessions sous la clé
   `<utilisateur>/<session_id>`. Les identifiants sont restreints à `[a-z0-9_-]` (32 caractères
   au plus) : ils servent de nom de fichier.

Les articles, le cache des réponses et les métriques restent communs : ce sont des données
publiques ou agrégées, sans information propre à un utilisateur.

## Alternatives considérées

- **OAuth 2.1 (spécification d'autorisation MCP)** — standard visé à terme, mais il faut un
  serveur d'autorisation, et les clients MCP ne le prennent pas tous en charge. Le jeton par
  utilisateur couvre le besoin d'une petite équipe sans infrastructure en plus ; le passage à
  OAuth ne changera que l'étape 1, puisque l'isolation repose seulement sur `current_user`.
- **Identifiant de session MCP (`Mcp-Session-Id`)** — un utilisateur qui se reconnecte en
  obtient un nouveau : ses préférences seraient perdues à chaque reconnexion.
- **Passer l'utilisateur en paramètre à chaque handler** — modifie toutes les signatures et
  laisse la porte ouverte à un oubli, donc à une fuite ; la `ContextVar` couvre d'office tout
  le code exécuté pendant l'appel, y compris dans `asyncio.to_thread`.
- **Préférences en base SQLite** — utile avec plusieurs instances, prématuré tant qu'une seule
  tourne (ADR-002) ; les fichiers JSON gardent le format existant.

## Conséquences

- Ajouter, retirer ou changer le jeton d'un utilisateur demande de modifier `NOVIT_API_TOKENS`
  et redémarre l'instance, comme pour `NOVIT_API_TOKEN`.
- Les jetons sont des secrets partagés hors bande ; pas de révocation fine ni d'expiration.
- Les sessions restent en mémoire : elles sont perdues au redémarrage, comme avant.
- Avec plusieurs instances, les préférences devront passer dans une base partagée (ADR-002).
