# Exemples de requêtes NovIT

Exemples concrets question → réponse attendue, par profil. Les réponses ci-dessous sont
illustratives (contenu d'articles fictif) — la structure exacte (en-têtes, emoji) suit
[RESPONSE_FORMATS.md](RESPONSE_FORMATS.md), gelée par `tests/test_prompt_regression.py`. Pour
les conseils de formulation généraux, voir [PROMPTING_GUIDE.md](PROMPTING_GUIDE.md).

---

## Profil ETUDIANT

### 1. Actualités du jour, sans précision

**Q :** « Quoi de neuf en IA aujourd'hui ? »
**R attendue :** `novit_get_news(profil="ETUDIANT", domaines=["ia"], periode="24h")` →
liste d'articles vulgarisés, ton pédagogique, sources accessibles en priorité (Hacker News,
dev.to, The Verge).

### 2. Découverte sans domaine précis

**Q :** « Montre-moi des trucs intéressants en tech »
**R attendue :** NovIT demande de préciser le profil/domaine s'ils sont inconnus, sinon utilise
les domaines favoris par défaut (`ia`, `dev`, `formation` pour ETUDIANT).

### 3. Premier contact / onboarding

**Q :** « Salut, c'est quoi NovIT ? »
**R attendue :** `novit_start()` → message de bienvenue + sélection de profil si non défini.

### 4. Résumé quotidien pédagogique

**Q :** « Fais-moi un résumé de la journée tech »
**R attendue :** `novit_daily(profil="ETUDIANT")` → groupé par domaine avec emoji, max 3
articles/domaine, ton accessible.

### 5. Recherche simple

**Q :** « Cherche des articles sur les LLM open source »
**R attendue :** `novit_search(query="LLM open source")` → résultats paginés, expliqués
simplement si le sujet est technique.

### 6. Creuser un article

**Q :** « Cet article a l'air intéressant, tu peux m'en dire plus ? https://example.com/llm-news »
**R attendue :** `novit_dig(url="https://example.com/llm-news")` → contenu extrait, résumé en
langage accessible par Claude.

### 7. Découverte insolite

**Q :** « Surprends-moi avec un truc inhabituel »
**R attendue :** `novit_unusual(count=3)` → articles avec un score de surprise élevé, hors des
sentiers battus.

### 8. Changer de profil

**Q :** « En fait je suis développeur, pas étudiant »
**R attendue :** `novit_set_profile(profil="INGENIEUR")` → confirmation, persistance dans les
préférences pour les prochaines sessions.

### 9. Filtrer par domaine de formation

**Q :** « Des ressources pour apprendre Rust ? »
**R attendue :** `novit_get_by_domain(domaine="formation", profil="ETUDIANT")` → tutoriels,
guides, contenus pédagogiques.

### 10. Comprendre un acronyme/actu

**Q :** « C'est quoi cette histoire de "AI Act" dont tout le monde parle ? »
**R attendue :** `novit_search(query="AI Act")` puis explication vulgarisée par Claude à partir
des articles trouvés (domaine `reglementation`).

---

## Profil INGENIEUR

### 1. Veille sécurité ciblée

**Q :** « News sécurité des dernières 6h »
**R attendue :** `novit_get_news(profil="INGENIEUR", domaines=["securite"], periode="6h")` →
CVE/alertes en priorité (NVD, ANSSI), ton concis et technique.

### 2. CVE critiques

**Q :** « Y a-t-il des CVE critiques cette semaine ? »
**R attendue :** `novit_get_by_domain(domaine="securite", profil="INGENIEUR")` → filtré sur les
CVE à fort CVSS (`CVEScraper`, seuil par défaut 7.0).

### 3. Résumé quotidien technique

**Q :** « Résumé de veille du jour sur tous mes domaines »
**R attendue :** `novit_daily(profil="INGENIEUR")` → groupé par domaine favori (`securite`,
`ingenierie`, `ia`, `dev`), niveau de détail « détaillé ».

### 4. Multi-domaines combinés

**Q :** « News IA et ingénierie des 48 dernières heures »
**R attendue :** `novit_get_news(profil="INGENIEUR", domaines=["ia", "ingenierie"], periode="24h")`
— NovIT n'a pas de fenêtre « 48h » native (valeurs possibles : `1h`, `6h`, `24h`, `7j`), Claude
reformule vers `24h` ou `7j` selon l'intention, à préciser si ambigu.

### 5. Recherche par source

**Q :** « Cherche "kubernetes" uniquement sur GitHub Trending »
**R attendue :** `novit_search(query="kubernetes", source="github_trending")` → résultats
filtrés à cette seule source.

### 6. Tendances

**Q :** « Quels sujets montent en ce moment ? »
**R attendue :** `novit_trends(days=7, top_k=10)` → sujets fréquents + section « en montée
rapide » si le ratio 24h/période dépasse le seuil.

### 7. Articles similaires

**Q :** « Des articles dans le même genre que celui-ci : https://example.com/rust-async »
**R attendue :** `novit_related(url="https://example.com/rust-async", domaines=["dev"])` →
similarité Jaccard domaines + titre, triés par score décroissant.

### 8. Approfondissement technique

**Q :** « Creuse cet article sur le nouveau protocole de consensus »
**R attendue :** `novit_dig(url="...")` → extraction complète, tronquée à 4000 caractères,
Claude peut ensuite répondre à des questions précises dessus.

### 9. État du système

**Q :** « NovIT, tu te portes bien ? »
**R attendue :** `novit_health(detail="global")` → statut, uptime, stats cache. (`detail=
"sources"` retourne actuellement une liste vide — limitation connue, voir
[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md#2-modules).)

### 10. Filtrage par période courte et domaine strict

**Q :** « Uniquement les CVE avec un CVSS supérieur à 8, dernière heure »
**R attendue :** NovIT ne filtre pas nativement par seuil CVSS exact via un paramètre d'outil —
Claude appelle `novit_get_by_domain(domaine="securite", profil="INGENIEUR")` puis filtre/reformule
la réponse selon le seuil demandé. Bonne pratique de prompting : voir
[PROMPTING_GUIDE.md — Conseils avancés](PROMPTING_GUIDE.md#conseils-avancés).

---

## Requêtes avancées (chaînage, ambiguïté, erreurs)

### Chaînage d'outils

**Q :** « Donne-moi les news IA, puis creuse le premier article »
**R attendue :** deux appels successifs — `novit_get_news(...)` puis `novit_dig(url=...)` avec
l'URL du premier résultat retourné par le premier appel.

### Requête ambiguë (ni profil ni domaine)

**Q :** « Donne-moi des news »
**R attendue :** pas d'appel d'outil immédiat — Claude demande de préciser profil et/ou domaine
(voir [ERROR_HANDLING_GUIDE.md — Requête ambiguë](ERROR_HANDLING_GUIDE.md#requête-ambiguë)).

### Domaine invalide

**Q :** « News sur le domaine "blockchain" » *(domaine non reconnu par NovIT)*
**R attendue :** `NovitError(NOVIT_INVALID_DOMAIN)` → Claude propose les domaines réels
disponibles (`ia, securite, dev, ingenierie, reglementation, formation`) — voir
[ADDING_A_DOMAIN.md](ADDING_A_DOMAIN.md) pour en ajouter un nouveau si le besoin est récurrent.

### Recherche + pagination

**Q :** « Cherche "rate limiting", page 2 »
**R attendue :** `novit_search(query="rate limiting", page=2, per_page=10)`.
