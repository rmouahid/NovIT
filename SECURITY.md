# Politique de sécurité

## Versions prises en charge

Seule la dernière version publiée reçoit des correctifs de sécurité. Avant la
v1.0, les correctifs sont livrés sur la branche `dev` puis dans la version
suivante.

## Signaler une vulnérabilité

**N'ouvrez pas d'issue publique.** Utilisez le signalement privé de GitHub :
onglet [Security → Report a vulnerability](https://github.com/rmouahid/NovIT/security/advisories/new).

Indiquez :

- la version de NovIT et le transport utilisé (stdio ou HTTP) ;
- les étapes pour reproduire, et l'impact constaté (lecture de données,
  contournement du jeton `NOVIT_API_TOKEN`, exécution de code, etc.) ;
- si possible, une proposition de correctif.

## Ce qui se passe ensuite

| Étape | Délai |
|---|---|
| Accusé de réception | 48 h |
| Évaluation et sévérité partagées avec vous | 7 jours |
| Correctif ou contournement publié | 7 jours après confirmation pour une faille critique, version suivante sinon |
| Avis de sécurité GitHub publié | à la sortie du correctif, avec crédit si vous le souhaitez |

## Périmètre

Sont concernés le serveur MCP NovIT, ses scrapers et son transport HTTP. Les
failles des sources externes (flux RSS, API tierces) sont à signaler à leurs
éditeurs. La rotation des secrets est décrite dans
[docs/SECRET_ROTATION.md](docs/SECRET_ROTATION.md).
