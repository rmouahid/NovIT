# NovIT — Milestones & Issues

> Outil MCP de veille technologique — _novit_ : "il sait, il connaît" + IT
> Document de planification complet · Version 1.0 · Juin 2026

---

## Vue d'ensemble

| Milestone | Objectif                              | Nb Issues     |
| --------- | ------------------------------------- | ------------- |
| M0        | Fondations du projet                  | 8             |
| M1        | Architecture MCP & serveur de base    | 10            |
| M2        | Scraping & sources de données         | 14            |
| M3        | Logique de veille & profils           | 12            |
| M4        | Prompt système & qualité des réponses | 9             |
| M5        | Interface & expérience utilisateur    | 8             |
| M6        | Tests, robustesse & monitoring        | 12            |
| M7        | Documentation & onboarding            | 8             |
| M8        | Collaboration & scalabilité           | 10            |
| M9        | Release publique                      | 7             |
| **Total** |                                       | **98 issues** |

---

## M0 — Fondations du projet

> **Objectif :** Avoir un repo propre, un environnement de dev fonctionnel et les bases techniques posées avant d'écrire la première ligne de code métier.

### Issues

- [ ] `chore` `P0` **Créer le repo GitHub NovIT**
  - Initialiser avec README, .gitignore Python, LICENSE (MIT)
  - Créer les branches `main` et `dev`
  - Protéger la branche `main` (PR obligatoire)

- [ ] `chore` `P0` **Définir la structure des dossiers du projet**

  ```
  novit/
  ├── src/
  │   ├── mcp/          # Serveur MCP
  │   ├── scrapers/     # Scrapers par source
  │   ├── profiles/     # Logique de profils
  │   └── prompts/      # Prompts système
  ├── tests/
  ├── docs/
  ├── config/
  └── scripts/
  ```

- [ ] `chore` `P0` **Mettre en place l'environnement virtuel Python**
  - Créer `requirements.txt` et `requirements-dev.txt`
  - Documenter la procédure d'installation dans le README
  - Tester sur Python 3.11+

- [ ] `chore` `P0` **Configurer les variables d'environnement**
  - Créer `.env.example` avec toutes les clés nécessaires
  - Ajouter `.env` au `.gitignore`
  - Documenter chaque variable dans `.env.example`

- [ ] `chore` `P1` **Mettre en place les pre-commit hooks**
  - Configurer `black` pour le formatage
  - Configurer `flake8` ou `ruff` pour le linting
  - Configurer `isort` pour les imports
  - Ajouter un hook de vérification des secrets (detect-secrets)

- [ ] `chore` `P1` **Configurer le système de versioning**
  - Adopter Semantic Versioning (SemVer : MAJOR.MINOR.PATCH)
  - Créer `CHANGELOG.md` avec le format Keep a Changelog
  - Créer le fichier `VERSION` à la racine

- [ ] `doc` `P1` **Rédiger le README principal**
  - Description du projet et vision
  - Badges (version, licence, Python)
  - Instructions d'installation
  - Quickstart
  - Lien vers la documentation complète

- [ ] `doc` `P1` **Ajouter la documentation initiale dans /docs**
  - Cahier des charges en markdown
  - Fichier CONTRIBUTING.md (comment contribuer)
  - Fichier ARCHITECTURE.md (vision technique initiale)
  - Fichier ROADMAP.md (lien vers les milestones)

---

## M1 — Architecture MCP & serveur de base

> **Objectif :** Avoir un serveur MCP fonctionnel, connecté à Claude, capable de recevoir des requêtes et de renvoyer des réponses structurées — même avec des données fictives.

### Issues

- [ ] `chore` `P0` **Étudier et documenter le protocole MCP**
  - Lire la spécification officielle MCP
  - Lister les types de messages supportés
  - Identifier les contraintes et limitations
  - Écrire un résumé dans `docs/MCP_NOTES.md`

- [ ] `feature` `P0` **Créer le squelette du serveur MCP**
  - Choisir le framework (FastAPI recommandé)
  - Implémenter le point d'entrée principal
  - Gérer le cycle de vie du serveur (start/stop)
  - Valider que le serveur démarre sans erreur

- [ ] `feature` `P0` **Implémenter le handshake MCP avec Claude**
  - Gérer l'initialisation de la connexion
  - Implémenter la négociation de capacités
  - Tester la connexion depuis Claude.ai
  - Logger les échanges pour debug

- [ ] `feature` `P0` **Définir et implémenter les outils MCP de base**
  - `novit_get_news` : récupérer les dernières news
  - `novit_search` : rechercher dans les sources
  - `novit_get_by_domain` : filtrer par domaine
  - `novit_get_profile` : récupérer les infos d'un profil
  - Documenter chaque outil (nom, description, paramètres, réponse)

- [ ] `feature` `P0` **Implémenter la gestion des erreurs globale**
  - Définir les codes d'erreur NovIT
  - Gérer les timeouts
  - Gérer les erreurs de sources externes
  - Retourner des messages d'erreur clairs à Claude

- [ ] `feature` `P1` **Implémenter un système de cache basique**
  - Choisir la stratégie de cache (TTL par source)
  - Implémenter avec `cachetools` ou Redis
  - Définir les TTL par type de contenu (news = 1h, profil = 24h)
  - Ajouter des métriques de cache hit/miss

- [ ] `chore` `P1` **Mettre en place la configuration du serveur**
  - Fichier `config/settings.py` avec Pydantic Settings
  - Support des environnements (dev, staging, prod)
  - Validation des variables d'environnement au démarrage

- [ ] `chore` `P1` **Mettre en place le système de logging**
  - Configurer `loguru` ou `logging` structuré
  - Logs en JSON en production
  - Logs lisibles en développement
  - Rotation des fichiers de log

- [ ] `feature` `P1` **Implémenter un endpoint de health check**
  - `GET /health` : statut du serveur
  - `GET /health/sources` : statut de chaque source
  - `GET /health/cache` : statut du cache
  - Utilisé pour le monitoring

- [ ] `chore` `P2` **Dockeriser le serveur MCP**
  - Créer `Dockerfile` optimisé (multi-stage build)
  - Créer `docker-compose.yml` pour le dev local
  - Documenter les commandes Docker dans le README
  - Tester le démarrage en container

---

## M2 — Scraping & sources de données

> **Objectif :** Implémenter les scrapers pour toutes les sources définies dans le cahier des charges, avec une architecture modulaire et extensible.

### Issues

- [ ] `chore` `P0` **Concevoir l'architecture des scrapers**
  - Définir une classe abstraite `BaseScraper`
  - Standardiser le format de sortie (dataclass ou Pydantic)
  - Définir les champs : titre, url, résumé, date, source, domaines, profils
  - Documenter comment ajouter un nouveau scraper

- [ ] `feature` `P0` **Implémenter le scraper Hacker News**
  - Utiliser l'API officielle HN (pas de scraping HTML)
  - Récupérer les top stories et les new stories
  - Filtrer par score minimum configurable
  - Tagger automatiquement les domaines

- [ ] `feature` `P0` **Implémenter le scraper GitHub Trending**
  - Scraper `github.com/trending` (pas d'API officielle)
  - Filtrer par langage si spécifié
  - Extraire : repo, description, étoiles, langage
  - Gérer la rotation des user-agents

- [ ] `feature` `P0` **Implémenter le scraper CVE Details / ANSSI**
  - Récupérer les CVE récents (via NVD API)
  - Récupérer les alertes ANSSI (Cert-FR RSS)
  - Filtrer par score CVSS minimum
  - Format de sortie spécifique sécurité

- [ ] `feature` `P0` **Implémenter les scrapers RSS génériques**
  - Classe `RssScraper` réutilisable
  - Couvrir : dev.to, TechCrunch, The Verge, MIT Tech Review
  - Gérer les flux Atom et RSS 2.0
  - Déduplication par URL

- [ ] `feature` `P1` **Implémenter les scrapers blogs IA**
  - Anthropic Blog (RSS ou scraping)
  - OpenAI Blog
  - Google DeepMind Blog
  - Papers With Code (API disponible)
  - arXiv cs.AI et cs.LG (API officielle)

- [ ] `feature` `P1` **Implémenter les scrapers blogs ingénierie**
  - Netflix Tech Blog (Medium RSS)
  - Google Engineering Blog
  - Meta Engineering Blog
  - The New Stack (RSS)

- [ ] `feature` `P1` **Implémenter les scrapers réglementation**
  - CNIL (RSS)
  - EUR-Lex (API ou RSS pour l'AI Act)
  - W3C News (RSS)

- [ ] `feature` `P1` **Implémenter les scrapers formation/certifications**
  - freeCodeCamp (RSS)
  - Roadmap.sh (GitHub releases)
  - Stack Overflow Developer Survey (annuel)

- [ ] `chore` `P1` **Implémenter le gestionnaire de scrapers**
  - Classe `ScraperManager` qui orchestre tous les scrapers
  - Exécution parallèle avec `asyncio`
  - Gestion des timeouts par scraper
  - Rapport d'exécution (succès/échec par source)

- [ ] `feature` `P1` **Implémenter le système de déduplication**
  - Déduplication par URL exacte
  - Déduplication par similarité de titre (fuzzy matching)
  - Fenêtre temporelle configurable (ex : 24h)
  - Stockage des hashes en cache

- [ ] `chore` `P1` **Implémenter le système de rate limiting**
  - Respecter les politiques robots.txt
  - Délai configurable entre requêtes par domaine
  - Backoff exponentiel en cas d'erreur 429
  - User-agent configurable et honnête

- [ ] `feature` `P2` **Implémenter le tagger automatique de domaines**
  - Associer chaque article à un ou plusieurs domaines NovIT
  - Basé sur mots-clés + source + heuristiques
  - Configurable via fichier YAML
  - Permettre le tagging manuel de correction

- [ ] `chore` `P2` **Mettre en place le stockage temporaire des articles**
  - Choisir le backend (SQLite pour dev, PostgreSQL pour prod)
  - Schéma de la table `articles`
  - Rétention configurable (défaut : 7 jours)
  - Index sur date, source, domaine

---

## M3 — Logique de veille & profils

> **Objectif :** Implémenter la logique de personnalisation selon le profil utilisateur, le filtrage intelligent et la construction des réponses de veille.

### Issues

- [ ] `feature` `P0` **Définir et implémenter le système de profils**
  - Profil `ETUDIANT` : besoins, sources prioritaires, niveau de détail
  - Profil `INGENIEUR` : besoins, sources prioritaires, niveau de détail
  - Structure de profil extensible (futurs profils possibles)
  - Fichier de configuration `config/profiles.yaml`

- [ ] `feature` `P0` **Implémenter le moteur de filtrage par profil**
  - Pondération des sources selon le profil
  - Filtrage des domaines selon les préférences
  - Score de pertinence par article
  - Tri et sélection des top N articles

- [ ] `feature` `P0` **Implémenter l'outil `novit_get_news` complet**
  - Paramètres : profil, domaines, nb_articles, période
  - Appel au gestionnaire de scrapers
  - Application du filtrage par profil
  - Retour structuré prêt pour Claude

- [ ] `feature` `P0` **Implémenter l'outil `novit_search` complet**
  - Recherche plein texte dans les articles en cache
  - Filtres optionnels : domaine, source, date, profil
  - Scoring de pertinence (TF-IDF ou similaire)
  - Pagination des résultats

- [ ] `feature` `P1` **Implémenter les préférences utilisateur**
  - Sources favorites / exclues
  - Domaines favoris / exclus
  - Niveau de détail souhaité (résumé court / détaillé)
  - Fréquence de rafraîchissement préférée
  - Stockage en fichier JSON local (pas de BDD utilisateur pour commencer)

- [ ] `feature` `P1` **Implémenter l'outil `novit_dig` (creuser une info)**
  - Paramètre : URL ou titre d'un article
  - Récupération du contenu complet de la page
  - Extraction du texte principal (readability)
  - Résumé structuré retourné à Claude

- [ ] `feature` `P1` **Implémenter l'outil `novit_related` (articles liés)**
  - À partir d'un article, trouver des articles similaires
  - Basé sur les tags de domaine et les mots-clés
  - Limité aux articles en cache (7 derniers jours)
  - Retourner les 3-5 articles les plus pertinents

- [ ] `feature` `P1` **Implémenter le résumé de veille quotidien**
  - Sélection automatique des N meilleurs articles du jour
  - Un résumé par domaine si plusieurs domaines demandés
  - Format adapté au profil (étudiant vs ingénieur)
  - Heure de génération configurable

- [ ] `feature` `P2` **Implémenter la détection de tendances**
  - Identifier les sujets qui reviennent souvent sur 7 jours
  - Alerter si un sujet monte en popularité (ex: nouvelle faille)
  - Seuil de détection configurable
  - Intégré dans la réponse de veille quotidienne

- [ ] `feature` `P2` **Implémenter le mode "nouveautés insolites"**
  - Ciblé profil ETUDIANT
  - Sélectionner des articles hors des sentiers battus
  - Basé sur un score de "surprise" (popularité faible + contenu riche)
  - 1 à 3 articles par session

- [ ] `chore` `P2` **Implémenter la file d'attente de scraping**
  - File de tâches asynchrones (Celery ou asyncio Queue)
  - Priorité : sources critiques (CVE) > sources régulières
  - Planification des refresh par source
  - Dashboard de statut de la file

- [ ] `feature` `P2` **Implémenter le contexte de conversation**
  - Mémoriser les articles déjà montrés dans une session
  - Ne pas répéter le même article dans la même session
  - Permettre de naviguer (suivant/précédent) dans les résultats
  - Réinitialisation du contexte après 24h

---

## M4 — Prompt système & qualité des réponses

> **Objectif :** Définir et affiner le comportement de Claude quand il utilise NovIT, pour garantir des réponses de qualité, adaptées au profil et au format souhaité.

### Issues

- [ ] `doc` `P0` **Rédiger le prompt système principal NovIT**
  - Définir le rôle de Claude dans NovIT
  - Instructions de comportement général
  - Règles de formatage des réponses
  - Gestion des cas d'erreur (source indisponible, etc.)

- [ ] `doc` `P0` **Rédiger les prompts spécifiques par profil**
  - Prompt profil ETUDIANT : ton pédagogique, vulgarisation, enthousiasme
  - Prompt profil INGENIEUR : ton professionnel, concision, précision technique
  - Variables dynamiques injectées (domaines, préférences)
  - Tests A/B entre variantes de prompts

- [ ] `doc` `P0` **Définir le format de réponse standard NovIT**
  - Format pour une news (titre, source, résumé, lien, domaine)
  - Format pour une liste de news (avec séparateurs)
  - Format pour le résumé quotidien
  - Format pour le mode "creuser" (article complet résumé)

- [ ] `feature` `P1` **Implémenter l'injection dynamique de contexte**
  - Injecter le profil dans chaque appel Claude
  - Injecter les préférences utilisateur
  - Injecter la date/heure courante
  - Injecter les domaines actifs de la session

- [ ] `doc` `P1` **Rédiger les instructions de gestion des erreurs pour Claude**
  - Que dire si une source est down ?
  - Que dire si aucun article pertinent n'est trouvé ?
  - Que dire si la requête est ambiguë ?
  - Que dire si le profil n'est pas défini ?

- [ ] `feature` `P1` **Mettre en place l'évaluation de la qualité des réponses**
  - Définir des critères de qualité (pertinence, format, longueur)
  - Créer un jeu de cas de test représentatifs
  - Évaluation manuelle dans un premier temps
  - Documenter les résultats dans `docs/EVAL_RESULTS.md`

- [ ] `feature` `P1` **Implémenter la gestion multilingue basique**
  - Détection de la langue de la requête utilisateur
  - Réponse dans la même langue (FR ou EN pour commencer)
  - Sources en anglais toujours incluses (résumé traduit si besoin)
  - Paramètre `langue` dans les outils MCP

- [ ] `doc` `P2` **Créer un guide de prompting NovIT**
  - Comment formuler une bonne requête NovIT
  - Exemples de requêtes par cas d'usage
  - Ce que NovIT sait et ne sait pas faire
  - FAQ des erreurs courantes

- [ ] `feature` `P2` **Implémenter le mode verbose / debug**
  - Mode debug activable par l'utilisateur
  - Affiche les sources consultées
  - Affiche le nombre d'articles trouvés avant filtrage
  - Affiche le temps de réponse de chaque source

---

## M5 — Interface & expérience utilisateur

> **Objectif :** Rendre NovIT agréable à utiliser au quotidien depuis Claude, avec une expérience fluide, des commandes intuitives et une bonne gestion de l'onboarding.

### Issues

- [ ] `feature` `P0` **Implémenter la commande d'initialisation**
  - Commande `/novit start` ou déclenchée automatiquement
  - Détection du profil (si pas défini, demander)
  - Affichage du menu des domaines disponibles
  - Message de bienvenue personnalisé

- [ ] `feature` `P0` **Implémenter la sélection interactive du profil**
  - Si profil inconnu : demander étudiant ou ingénieur
  - Possibilité de changer de profil en cours de session
  - Mémorisation du profil pour les sessions suivantes
  - Confirmation visuelle du profil actif

- [ ] `feature` `P1` **Implémenter la sélection des domaines**
  - Afficher la liste des domaines disponibles
  - Permettre de sélectionner un ou plusieurs domaines
  - Raccourcis (ex: "tout", "cyber seulement", "IA + dev")
  - Domaines actifs affichés en début de session

- [ ] `feature` `P1` **Implémenter les commandes rapides**
  - `/novit news` : dernières news selon profil actif
  - `/novit daily` : résumé de veille du jour
  - `/novit search [terme]` : recherche
  - `/novit dig [url]` : creuser un article
  - `/novit help` : aide et liste des commandes

- [ ] `feature` `P1` **Implémenter le mode "flux continu"**
  - L'utilisateur peut demander "article suivant"
  - Navigation avant/arrière dans les résultats
  - Indicateur de position (ex: "3/15 articles")
  - Commande pour revenir au menu principal

- [ ] `feature` `P2` **Implémenter les alertes personnalisées**
  - L'utilisateur peut définir des mots-clés d'alerte
  - NovIT signale proactivement si un article contient ces mots
  - Niveaux d'alerte : info, important, critique
  - Gestion des faux positifs (feedback utilisateur)

- [ ] `feature` `P2` **Implémenter le résumé de session**
  - En fin de session (commande `/novit end`)
  - Afficher les articles consultés
  - Afficher les sujets tendance de la session
  - Option d'export en markdown

- [ ] `doc` `P2` **Rédiger le guide utilisateur NovIT**
  - Installation et connexion à Claude
  - Premier démarrage et configuration du profil
  - Guide des commandes avec exemples
  - Trucs et astuces pour tirer le meilleur de NovIT

---

## M6 — Tests, robustesse & monitoring

> **Objectif :** Garantir la fiabilité de NovIT avec une couverture de tests solide, une gestion des pannes et des outils de monitoring.

### Issues

- [ ] `chore` `P0` **Mettre en place le framework de tests**
  - Configurer `pytest` avec `pytest-asyncio`
  - Configurer `pytest-cov` pour la couverture
  - Définir un objectif de couverture (80% minimum)
  - Créer des fixtures réutilisables

- [ ] `test` `P0` **Écrire les tests unitaires des scrapers**
  - Test de chaque scraper avec des réponses mockées
  - Test de la gestion des erreurs HTTP (404, 500, timeout)
  - Test du parsing des données
  - Test de la déduplication

- [ ] `test` `P0` **Écrire les tests unitaires du serveur MCP**
  - Test de chaque outil MCP
  - Test de la gestion des paramètres invalides
  - Test des réponses d'erreur
  - Test du cache

- [ ] `test` `P1` **Écrire les tests d'intégration**
  - Test du flux complet (requête → scraping → filtrage → réponse)
  - Test de la connexion avec Claude (environnement de test)
  - Test de la persistance des préférences utilisateur
  - Test des profils ETUDIANT et INGENIEUR

- [ ] `test` `P1` **Écrire les tests de performance**
  - Temps de réponse cible : < 3s pour une requête standard
  - Test de charge : 10 requêtes simultanées
  - Test du cache : mesurer le gain de performance
  - Documenter les résultats dans `docs/PERF_RESULTS.md`

- [ ] `chore` `P1` **Mettre en place la CI/CD avec GitHub Actions**
  - Workflow `ci.yml` : lint + tests à chaque PR
  - Workflow `release.yml` : build + tag à chaque merge sur main
  - Rapport de couverture automatique (Codecov)
  - Badge de statut dans le README

- [ ] `feature` `P1` **Implémenter le circuit breaker par source**
  - Si une source échoue 3 fois de suite → la désactiver temporairement
  - Réactivation automatique après délai (ex: 30 min)
  - Notification dans les logs
  - Visible dans le health check

- [ ] `chore` `P1` **Mettre en place le monitoring des sources**
  - Vérification périodique de la disponibilité de chaque source
  - Historique de disponibilité (uptime par source)
  - Alerte si une source est down depuis plus de 2h
  - Dashboard de statut (simple fichier JSON ou Prometheus)

- [ ] `chore` `P2` **Mettre en place Sentry pour le tracking des erreurs**
  - Intégrer le SDK Sentry Python
  - Capturer les exceptions non gérées
  - Contexte enrichi (source, profil, outil MCP appelé)
  - Configuration par environnement

- [ ] `test` `P2` **Écrire les tests de régression des prompts**
  - Cas de test : requêtes standard par profil
  - Vérification du format de réponse attendu
  - Détection des régressions lors des changements de prompt
  - Automatisé dans la CI

- [ ] `chore` `P2` **Mettre en place les métriques applicatives**
  - Nombre de requêtes par outil MCP
  - Temps de réponse par source
  - Taux de cache hit
  - Nb d'articles par domaine et par profil
  - Exposition via endpoint `/metrics` (format Prometheus)

- [ ] `chore` `P2` **Implémenter la gestion de la rotation des secrets**
  - Documentation de la procédure de rotation des clés API
  - Rechargement des secrets sans redémarrage du serveur
  - Test de la continuité de service lors d'une rotation

---

## M7 — Documentation & onboarding

> **Objectif :** Rendre NovIT accessible, compréhensible et maintenable pour toi et pour de futurs contributeurs.

### Issues

- [ ] `doc` `P0` **Rédiger la documentation technique complète**
  - Architecture générale avec schéma
  - Description de chaque module
  - Description de chaque outil MCP (inputs/outputs)
  - Guide de débogage

- [ ] `doc` `P0` **Rédiger le guide d'installation complet**
  - Prérequis (Python, Claude, MCP)
  - Installation pas à pas
  - Configuration initiale
  - Vérification que tout fonctionne

- [ ] `doc` `P1` **Documenter comment ajouter une nouvelle source**
  - Template de scraper à copier
  - Étapes de développement et test
  - Comment soumettre une PR
  - Critères d'acceptation d'une nouvelle source

- [ ] `doc` `P1` **Documenter comment ajouter un nouveau domaine**
  - Modifier `config/domains.yaml`
  - Ajouter les mots-clés associés
  - Adapter les profils si nécessaire
  - Tester le tagging automatique

- [ ] `doc` `P1` **Créer un wiki GitHub**
  - Page d'accueil du wiki
  - FAQ technique
  - Décisions d'architecture (ADR — Architecture Decision Records)
  - Journal des changements importants

- [ ] `doc` `P2` **Rédiger les ADR (Architecture Decision Records)**
  - ADR-001 : Choix de FastAPI pour le serveur MCP
  - ADR-002 : Choix de SQLite en dev / PostgreSQL en prod
  - ADR-003 : Stratégie de cache (TTL par source)
  - ADR-004 : Choix du format de sortie standardisé
  - Template ADR pour les futures décisions

- [ ] `doc` `P2` **Créer des exemples de requêtes NovIT**
  - 10 exemples de requêtes typiques profil ETUDIANT
  - 10 exemples de requêtes typiques profil INGENIEUR
  - Exemples de requêtes avancées (multi-domaines, recherche)
  - Format : question → réponse attendue

- [ ] `doc` `P2` **Rédiger le post de présentation du projet**
  - Pour dev.to ou Medium
  - Contexte, problème, solution
  - Architecture en 5 minutes
  - Comment l'utiliser et contribuer

---

## M8 — Collaboration & scalabilité

> **Objectif :** Préparer NovIT à accueillir des contributeurs extérieurs et à monter en charge, sans refonte majeure de l'architecture.

### Issues

- [ ] `chore` `P0` **Définir la gouvernance du projet**
  - Rédiger le CODE_OF_CONDUCT.md
  - Définir le processus de contribution (CONTRIBUTING.md complet)
  - Définir les rôles : maintainer, contributor, reviewer
  - Définir le processus de release

- [ ] `chore` `P1` **Créer les templates GitHub**
  - Template d'issue : bug report
  - Template d'issue : feature request
  - Template d'issue : nouvelle source
  - Template de Pull Request
  - Template de discussion

- [ ] `feature` `P1` **Rendre la configuration des sources 100% déclarative**
  - Toutes les sources définies dans `config/sources.yaml`
  - Ajouter une source sans écrire de code (si RSS)
  - Valider le fichier de config au démarrage
  - Hot-reload de la config sans redémarrage

- [ ] `feature` `P1` **Implémenter le système de plugins de scrapers**
  - Interface claire pour développer un scraper externe
  - Chargement dynamique des scrapers depuis un dossier
  - Documentation du contrat d'interface
  - Exemple de scraper plugin dans `examples/`

- [ ] `chore` `P1` **Préparer le déploiement cloud**
  - Choisir la plateforme (Railway, Fly.io, ou VPS)
  - Créer les fichiers de configuration de déploiement
  - Variables d'environnement de production documentées
  - Script de déploiement automatisé

- [ ] `feature` `P2` **Implémenter le support multi-utilisateurs**
  - Profils utilisateurs isolés
  - Préférences stockées par utilisateur
  - Historique de session par utilisateur
  - Pas de fuite d'informations entre utilisateurs

- [ ] `chore` `P2` **Mettre en place la gestion des dépendances**
  - `dependabot` configuré pour les mises à jour automatiques
  - Politique de mise à jour des dépendances
  - Tests de non-régression après chaque mise à jour

- [ ] `feature` `P2` **Implémenter un système de feedback utilisateur**
  - Commande `/novit feedback [commentaire]`
  - Stockage des feedbacks avec contexte (profil, domaine, requête)
  - Rapport hebdomadaire de feedbacks
  - Lien avec les issues GitHub si bug signalé

- [ ] `chore` `P2` **Optimiser les performances de scraping**
  - Profiler les scrapers les plus lents
  - Identifier les goulots d'étranglement
  - Parallélisation maximale avec asyncio
  - Objectif : rafraîchissement complet en < 60s

- [ ] `feature` `P2` **Implémenter un mode hors-ligne dégradé**
  - Si toutes les sources sont down : servir le cache
  - Indiquer clairement que les données sont en cache
  - Âge des données affiché
  - Retry automatique en arrière-plan

---

## M9 — Release publique

> **Objectif :** Sortir NovIT v1.0 de manière propre, visible et maintenable, avec tout ce qu'il faut pour que d'autres puissent l'utiliser et contribuer.

### Issues

- [ ] `chore` `P0` **Préparer la release v1.0**
  - Audit final du code (sécurité, qualité, dette technique)
  - Mise à jour de toutes les dépendances
  - CHANGELOG.md complet depuis le début
  - Tag git `v1.0.0` sur main

- [ ] `chore` `P0` **Publier le package sur PyPI**
  - Créer le fichier `pyproject.toml`
  - Configurer le build avec `hatch` ou `flit`
  - Publier sur TestPyPI d'abord
  - Publier sur PyPI en production

- [ ] `chore` `P0` **Publier NovIT dans le registre MCP officiel**
  - Préparer la fiche de présentation MCP
  - Soumettre au registre officiel (si disponible)
  - Lien dans le README vers le registre

- [ ] `doc` `P0` **Créer la landing page du projet**
  - README enrichi avec GIF de démo
  - Captures d'écran des réponses NovIT dans Claude
  - Badges : version, PyPI, tests, licence
  - Call to action : installer / contribuer / signaler un bug

- [ ] `chore` `P1` **Publier le post de lancement**
  - Article dev.to ou Medium
  - Post LinkedIn / X (si souhaité)
  - Post sur les communautés pertinentes (HN, Reddit r/MachineLearning)
  - Répondre aux premiers retours

- [ ] `chore` `P1` **Mettre en place le support post-release**
  - Process de triage des issues entrantes
  - SLA de réponse (ex: 48h pour les bugs critiques)
  - Roadmap publique v1.1 publiée
  - Canal de communication (Discord ou Discussions GitHub)

- [ ] `chore` `P2` **Bilan et retrospective v1.0**
  - Ce qui a bien marché
  - Ce qui aurait pu être mieux fait
  - Décisions à réévaluer pour la v2
  - Document `docs/RETROSPECTIVE_V1.md`

---

## Labels recommandés

| Label              | Couleur   | Usage                               |
| ------------------ | --------- | ----------------------------------- |
| `feature`          | `#0075ca` | Nouvelle fonctionnalité             |
| `chore`            | `#e4e669` | Tâche technique sans valeur directe |
| `doc`              | `#0052cc` | Documentation                       |
| `test`             | `#d93f0b` | Tests                               |
| `bug`              | `#ee0701` | Correction de bug                   |
| `P0`               | `#b60205` | Priorité critique — bloquant        |
| `P1`               | `#e99695` | Priorité haute — important          |
| `P2`               | `#f9d0c4` | Priorité normale — nice to have     |
| `good first issue` | `#7057ff` | Bon pour les nouveaux contributeurs |
| `help wanted`      | `#008672` | Aide externe bienvenue              |
| `wontfix`          | `#ffffff` | Ne sera pas traité                  |

---

## Ordre de développement recommandé

```
M0 (fondations) → M1 (MCP de base) → M2 (scrapers) → M3 (logique)
     ↓
M4 (prompts) → M5 (UX) → M6 (tests)
     ↓
M7 (doc) → M8 (collaboration) → M9 (release)
```

Les milestones M6 (tests) et M7 (doc) doivent être alimentés **en continu** dès M1, pas seulement à la fin.

---

_NovIT — Il connaît l'IT · Planification v1.0 · Juin 2026_
