# Guide de prompting NovIT

## Comment formuler une bonne requête

### Exemples par cas d'usage

| Ce que tu veux | Comment le demander |
|---|---|
| Actualités du jour | "Quoi de neuf en IA aujourd'hui ?" |
| Veille ciblée | "News sécurité des dernières 6h, profil INGENIEUR" |
| Résumé complet | "Résumé de veille du jour sur tous mes domaines" |
| Creuser un article | "Creuse cet article : https://..." |
| Recherche | "Cherche des articles sur Rust async" |
| Tendances | "Quels sujets montent en ce moment ?" |
| Insolite | "Surprends-moi avec quelque chose d'inhabituel" |
| Similaires | "Articles dans le même genre que celui-ci : https://..." |
| État système | "NovIT, tu te portes bien ?" |

---

## Ce que NovIT sait faire

- Récupérer les actualités de **15+ sources** (HN, GitHub, CVE, arXiv, blogs tech…)
- Filtrer selon ton **profil** (ETUDIANT ou INGENIEUR) et tes **domaines** préférés
- **Résumer** les articles pour aller à l'essentiel
- **Chercher** dans les articles récents en base
- Détecter les **tendances** des 7 derniers jours
- **Creuser** n'importe quel lien pour en extraire le contenu

## Ce que NovIT ne fait pas

- Donner des avis ou des recommandations personnelles (sauf si demandé)
- Inventer des articles ou des informations
- Couvrir l'actu générale (politique, sport, économie…)
- Accéder aux articles derrière un paywall

---

## FAQ des erreurs courantes

**"NovIT ne trouve rien"**
→ Les sources sont peut-être vides. Essaie d'élargir la période : "news de la semaine" au lieu de "news du jour".

**"Les articles ne correspondent pas à mon domaine"**
→ Précise le domaine dans ta requête : "news IA" et non juste "news".

**"NovIT répond en anglais"**
→ Écris ta requête en français, NovIT répond dans la même langue.

**"Je veux changer de profil"**
→ Dis simplement "change mon profil pour ETUDIANT" ou "passe en mode INGENIEUR".

**"Comment voir d'où viennent les articles ?"**
→ Demande "active le mode debug" ou passe le paramètre `debug=true` dans l'outil.

---

## Conseils avancés

- **Chaîner les requêtes** : "donne-moi les news IA, puis creuse le premier article"
- **Affiner progressivement** : commence large, puis filtre avec "uniquement les CVE CVSS > 8"
- **Combiner domaines** : "news IA et ingénierie des 48 dernières heures"
- **Naviguer** : "article suivant" ou "reviens en arrière" dans les résultats
