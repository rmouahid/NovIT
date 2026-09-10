# Notes sur le protocole MCP — Model Context Protocol

> Résumé technique à usage interne · Juin 2026

---

## Qu'est-ce que MCP ?

MCP (Model Context Protocol) est un protocole standardisé open-source développé par Anthropic qui permet à des LLMs (Claude en premier lieu) de communiquer avec des serveurs externes exposant des **ressources**, des **outils** et des **prompts**.

C'est l'équivalent de "plugins" pour Claude, mais avec un protocole formel basé sur JSON-RPC 2.0.

**Spec officielle :** https://modelcontextprotocol.io/docs/

---

## Architecture générale

```
┌─────────────────────────────────────┐
│           Hôte MCP                  │
│  (Claude Desktop, Claude.ai, etc.)  │
│                                     │
│  ┌─────────────┐                    │
│  │  LLM Claude │                    │
│  └──────┬──────┘                    │
│         │ décide d'utiliser un outil│
│  ┌──────▼──────────────────────┐    │
│  │     Client MCP (intégré)    │    │
│  └──────┬──────────────────────┘    │
└─────────┼───────────────────────────┘
          │ JSON-RPC 2.0 (stdio ou HTTP/SSE)
┌─────────▼───────────────────────────┐
│         Serveur MCP (NovIT)         │
│  Expose : outils, ressources,       │
│           prompts                   │
└─────────────────────────────────────┘
```

---

## Transport

MCP supporte deux modes de transport :

| Mode | Protocole | Usage |
|---|---|---|
| **stdio** | stdin/stdout JSON-RPC | Dev local, Claude Desktop |
| **HTTP + SSE** | HTTP POST + Server-Sent Events | Déploiement cloud, remote |

Pour NovIT en développement local : **stdio** (plus simple, aucun réseau).
Pour le déploiement cloud (M8) : **HTTP + SSE**.

---

## Cycle de vie d'une connexion

```
Client                          Serveur NovIT
  │                                  │
  │──── initialize ─────────────────▶│  Envoie version, capacités client
  │◀─── initialized ─────────────────│  Répond version, capacités serveur
  │                                  │
  │──── tools/list ─────────────────▶│  Liste les outils disponibles
  │◀─── [liste d'outils] ────────────│
  │                                  │
  │──── tools/call ─────────────────▶│  Appelle un outil avec paramètres
  │◀─── [résultat] ──────────────────│
  │                                  │
  │──── notifications/cancelled ────▶│  (optionnel) Annule une requête
  │                                  │
  │──── (connexion fermée) ──────────│
```

---

## Types de messages MCP

### Requests (client → serveur)

| Message | Description |
|---|---|
| `initialize` | Démarre la connexion, négocie les capacités |
| `tools/list` | Liste les outils exposés par le serveur |
| `tools/call` | Exécute un outil avec ses paramètres |
| `resources/list` | Liste les ressources disponibles |
| `resources/read` | Lit le contenu d'une ressource |
| `prompts/list` | Liste les prompts disponibles |
| `prompts/get` | Récupère un prompt avec ses arguments |
| `ping` | Vérifie que le serveur est vivant |

### Notifications (serveur → client)

| Message | Description |
|---|---|
| `notifications/tools/list_changed` | Signal que la liste des outils a changé |
| `notifications/resources/updated` | Une ressource a été mise à jour |
| `notifications/progress` | Progression d'une opération longue |

---

## Format d'un outil MCP

```json
{
  "name": "novit_get_news",
  "description": "Récupère les dernières actualités tech filtrées selon le profil utilisateur.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "profil": {
        "type": "string",
        "enum": ["ETUDIANT", "INGENIEUR"],
        "description": "Profil utilisateur pour filtrer et adapter les résultats"
      },
      "domaines": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Domaines à couvrir : ia, securite, dev, ingenierie, reglementation, formation"
      },
      "nb_articles": {
        "type": "integer",
        "default": 10,
        "description": "Nombre d'articles à retourner"
      },
      "periode": {
        "type": "string",
        "enum": ["1h", "6h", "24h", "7j"],
        "default": "24h",
        "description": "Fenêtre temporelle des articles"
      }
    },
    "required": ["profil"]
  }
}
```

---

## Format d'une réponse d'outil

```json
{
  "content": [
    {
      "type": "text",
      "text": "# Veille NovIT — 10 articles · Profil INGENIEUR\n\n..."
    }
  ],
  "isError": false
}
```

En cas d'erreur :
```json
{
  "content": [
    {
      "type": "text",
      "text": "Erreur NovIT [NOVIT_SOURCE_UNAVAILABLE] : La source Hacker News est temporairement indisponible."
    }
  ],
  "isError": true
}
```

---

## Capacités (capabilities)

Lors du `initialize`, chaque partie déclare ses capacités :

```json
{
  "capabilities": {
    "tools": {},
    "resources": { "subscribe": true },
    "prompts": {},
    "logging": {}
  }
}
```

NovIT expose : **tools** + **resources** (articles en cache) + **prompts** (templates).

---

## Contraintes et limitations identifiées

1. **Taille des réponses** : Claude a une fenêtre de contexte limitée. Les réponses MCP doivent rester concises (< 10 000 tokens recommandé). NovIT doit donc tronquer/résumer les articles longs.
2. **Pas d'état côté client** : chaque appel d'outil est indépendant. Le contexte de session doit être maintenu côté serveur NovIT.
3. **Timeout** : Claude Desktop coupe la connexion après un délai (variable selon la version). Viser < 5s par appel d'outil.
4. **stdio en dev** : le serveur ne peut pas écrire sur stdout en dehors des messages JSON-RPC (les logs doivent aller sur stderr).
5. **Pas de WebSocket** : le transport HTTP+SSE est unidirectionnel serveur→client pour les notifications. Les requêtes restent client→serveur en HTTP POST.

---

## SDK Python disponible

```bash
pip install mcp
```

Le SDK `mcp` fournit :
- `Server` : classe de base pour implémenter un serveur MCP
- `@server.tool()` : décorateur pour enregistrer un outil
- `@server.resource()` : décorateur pour une ressource
- Gestion automatique du handshake et du transport stdio/HTTP

Voir `src/mcp/server.py` pour l'implémentation NovIT.
