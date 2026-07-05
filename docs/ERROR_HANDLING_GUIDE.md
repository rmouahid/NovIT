# Guide de gestion des erreurs — NovIT pour Claude

Ce document définit comment Claude doit réagir face aux situations d'erreur
renvoyées par les outils MCP NovIT. L'objectif : rester utile même quand
quelque chose ne fonctionne pas.

---

## Erreurs par code NovIT

### `SOURCE_UNAVAILABLE` — Source indisponible

**Situation :** Un scraper n'a pas pu joindre sa source (timeout réseau, site down).

**Réponse attendue :**
> ⚠️ La source **{nom_source}** est temporairement indisponible.
> J'ai continué avec les autres sources disponibles.
> Voici les résultats :

Ne pas bloquer — utiliser les sources restantes et le mentionner.

---

### `SOURCE_TIMEOUT` — Délai dépassé

**Situation :** La source a répondu mais trop lentement (> 30s).

**Réponse attendue :**
> ⏱ **{nom_source}** n'a pas répondu dans les délais.
> Les résultats ci-dessous proviennent des autres sources.

---

### `NO_RESULTS` — Aucun résultat

**Situation :** Aucun article ne correspond aux critères (domaine + profil + période).

**Réponse attendue :**
> Aucun article trouvé pour {critères}.
>
> Suggestions :
> - Élargir la période (ex: 7 jours au lieu de 24h)
> - Essayer d'autres domaines : {domaines_alternatifs}
> - Lancer une mise à jour des sources : demande-moi "mets à jour les sources"

Ne jamais inventer d'articles.

---

### `INVALID_PROFILE` — Profil inconnu

**Situation :** Le profil demandé n'existe pas dans la configuration.

**Réponse attendue :**
> Je ne connais pas le profil "{nom_profil}".
> Les profils disponibles sont : **ETUDIANT** et **INGENIEUR**.
> Lequel souhaitez-vous utiliser ?

Toujours proposer une alternative concrète.

---

### `INVALID_DOMAIN` — Domaine non reconnu

**Situation :** Le domaine demandé n'est pas dans la liste NovIT.

**Réponse attendue :**
> Le domaine "{domaine}" n'est pas dans ma base.
> Domaines disponibles : ia, securite, dev, ingenierie, reglementation, formation
> Je peux chercher dans tous les domaines si tu veux.

---

### `SCRAPING_ERROR` — Erreur interne scraping

**Situation :** Erreur imprévue lors du scraping (parsing, changement de format, etc.).

**Réponse attendue :**
> J'ai rencontré un problème technique avec **{nom_source}**.
> Ce problème a été enregistré automatiquement.
> Les autres sources fonctionnent normalement.

Ne pas afficher le traceback Python à l'utilisateur.

---

## Cas spéciaux

### Requête ambiguë
L'utilisateur demande "donne moi des news" sans préciser profil ni domaine.

**Réponse :**
> Pour personnaliser ta veille, j'ai besoin de savoir :
> 1. Ton profil : **ETUDIANT** ou **INGENIEUR** ?
> 2. Domaines souhaités (ou tous) : ia, securite, dev, ingenierie…

### Aucun profil défini
Premier usage sans profil configuré.

**Réponse :**
> Bienvenue sur NovIT ! Pour commencer, dis-moi :
> - Tu es **étudiant(e)** en IT ou en reconversion ?
> - Ou **ingénieur(e)** / développeur(se) en poste ?

### Requête hors périmètre
L'utilisateur demande quelque chose que NovIT ne fait pas (rédiger du code, etc.).

**Réponse :**
> NovIT est spécialisé dans la veille technologique.
> Pour {demande}, je te suggère de me demander directement sans NovIT.
> En veille, je peux : news, recherche, tendances, résumé quotidien.
