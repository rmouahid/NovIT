# Résultats d'évaluation NovIT

## Critères de qualité

| Critère | Description | Poids |
|---|---|---|
| **Pertinence** | L'article est-il dans le bon domaine ? | 30% |
| **Fraîcheur** | L'article date de moins de 24h ? | 20% |
| **Format** | Respect du template de réponse ? | 20% |
| **Résumé** | Résumé utile et fidèle ? | 20% |
| **Longueur** | Ni trop court ni trop verbeux ? | 10% |

Score global = somme pondérée. Seuil acceptable : ≥ 0.7.

---

## Cas de test représentatifs

### CAS-01 — News IA profil ETUDIANT
- **Requête :** "quoi de neuf en IA ?"
- **Profil :** ETUDIANT
- **Attendu :** 3-5 articles domaine `ia`, résumés vulgarisés, enthousiasme
- **Vérifier :** Présence de "💡 Pour aller plus loin" ou ressource supplémentaire

### CAS-02 — CVE profil INGENIEUR
- **Requête :** "dernières failles sécurité"
- **Profil :** INGENIEUR
- **Attendu :** CVEs avec CVSS, vecteur d'attaque, statut patch
- **Vérifier :** Format `CVSS X.X`, pas de vulgarisation inutile

### CAS-03 — Recherche textuelle
- **Requête :** "recherche kubernetes"
- **Profil :** indifférent
- **Attendu :** Articles contenant "kubernetes" triés par pertinence
- **Vérifier :** Résultats paginés, score de pertinence cohérent

### CAS-04 — Source indisponible
- **Simulation :** Désactiver HackerNews
- **Attendu :** Réponse avec avertissement + résultats des autres sources
- **Vérifier :** Pas d'erreur Python exposée, mention de la source indispo

### CAS-05 — Résumé quotidien
- **Requête :** "résumé de veille du jour"
- **Profil :** INGENIEUR
- **Attendu :** Format quotidien avec sections par domaine
- **Vérifier :** Emojis présents, max 3/domaine, heure UTC en pied de page

### CAS-06 — Aucun résultat
- **Simulation :** Requête domaine vide (ex: "reglementation" sans articles)
- **Attendu :** Message d'erreur constructif avec suggestions
- **Vérifier :** Pas d'invention d'articles, proposition d'alternative

---

## Résultats d'évaluation manuelle

_Évaluation initiale à compléter après première intégration Claude._

| Cas | Pertinence | Fraîcheur | Format | Résumé | Longueur | Score |
|---|---|---|---|---|---|---|
| CAS-01 | — | — | — | — | — | — |
| CAS-02 | — | — | — | — | — | — |
| CAS-03 | — | — | — | — | — | — |
| CAS-04 | — | — | — | — | — | — |
| CAS-05 | — | — | — | — | — | — |
| CAS-06 | — | — | — | — | — | — |

---

## Procédure d'évaluation

1. Lancer le serveur NovIT en local : `python -m src.mcp.server`
2. Connecter Claude Desktop avec la config MCP
3. Jouer chaque cas et noter les scores (0.0 à 1.0 par critère)
4. Mettre à jour ce fichier avec les résultats
5. Si score < 0.7 : ouvrir une issue `quality` pour investigation
