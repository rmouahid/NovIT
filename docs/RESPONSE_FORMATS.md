# Formats de réponse NovIT

Ce document définit les templates de sortie que NovIT produit pour chaque type de réponse.
Ces formats sont produits par les handlers Python et validés dans les tests.

---

## Format 1 — News unitaire

```markdown
### [Titre de l'article](https://url-de-l-article)
📰 NomSource · 📅 JJ/MM/AAAA · 🏷 domaine1, domaine2
> Résumé en 1-3 phrases maximum.
```

**Règles :**
- Titre = titre original de l'article (non tronqué)
- Date format `JJ/MM` si aujourd'hui ou hier, `JJ/MM/AAAA` sinon
- Résumé : 100-200 caractères, en français
- Score de pertinence non affiché à l'utilisateur

---

## Format 2 — Liste de news

```markdown
## Actualités {domaine} — {période}
_{N} articles · Profil {PROFIL}_

**1.** [Titre](url) — NomSource · 📅 date
> Résumé court.

**2.** [Titre](url) — NomSource · 📅 date
> Résumé court.
```

**Règles :**
- En-tête obligatoire avec domaine, période et nombre d'articles
- Numérotation si >= 3 articles
- Résumé limité à 100 caractères dans les listes
- Séparateur `---` entre sections de domaines différents

---

## Format 3 — Résumé quotidien

```markdown
# Veille quotidienne NovIT
**Mardi 20 Janvier 2026** · Profil INGENIEUR

## 🤖 Intelligence Artificielle
- **[Titre article 1](url)** · Source · 14:30
  _Résumé court en italique_
- **[Titre article 2](url)** · Source · 09:15

## 🔐 Cybersécurité
- **[Titre CVE](url)** · NVD · 11:00

---
_6 articles sélectionnés · Généré à 16:00 UTC_
```

**Règles :**
- Emoji de domaine : 🤖 IA, 🔐 Sécurité, 💻 Dev, ⚙️ Ingénierie, 📜 Réglementation, 📚 Formation
- Maximum 3 articles par domaine
- Pied de page avec total et heure UTC

---

## Format 4 — Mode "creuser" (novit_dig)

```markdown
# [Titre complet de l'article](url-originale)
📰 Source · 📅 Date · ⏱ Lecture ~N min

## Résumé
{résumé extrait ou généré en 3-5 phrases}

## Points clés
- Point 1
- Point 2
- Point 3

## Contenu
{corps de l'article extrait, reformaté, tronqué à 4000 chars}

---
🔗 [Lire l'article complet](url-originale)
```

**Règles :**
- Temps de lecture estimé : len(texte) / 1000 * 0.5 minutes
- Section "Points clés" uniquement si 3+ paragraphes détectés
- Contenu tronqué à 4000 caractères avec `…` en fin

---

## Format 5 — Articles similaires (novit_related)

```markdown
## Articles similaires à "{titre-reference}"
_Similarité basée sur domaines + mots-clés du titre_

1. **[Titre](url)** — Source — {score*100:.0f}% similaire
   🏷 domaine1, domaine2

2. **[Titre](url)** — Source — {score*100:.0f}% similaire
```

---

## Format 6 — Tendances (novit_trends)

```markdown
# Tendances NovIT — 7 derniers jours
_Analysé à 16:00 UTC · 243 articles_

## Sujets les plus fréquents
- **kubernetes** (18×) ██████████████████
- **llm** (14×) ██████████████

## 🚀 En montée rapide (dernières 24h)
- **agent** — 5× aujourd'hui (×3.2 vs moyenne)
```
