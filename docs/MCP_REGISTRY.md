# Publication dans le registre MCP

Le manifeste [server.json](../server.json) prépare l'inscription sous
`io.github.rmouahid/novit`. Sa présence dans le dépôt ne signifie pas que
le serveur est publié. L'inscription reste à vérifier après publication.

## Prérequis et ordre de publication

1. Construire et publier le paquet sur TestPyPI, puis PyPI selon
   [PUBLISHING.md](PUBLISHING.md). Le registre MCP consulte PyPI, pas
   TestPyPI. Le README de la version publiée doit contenir le marqueur
   `mcp-name: io.github.rmouahid/novit` ; modifier seulement le dépôt ne
   modifie pas une distribution déjà publiée.
2. Aligner `version` et `packages[0].version` de `server.json` avec `VERSION`.
   Si la version PyPI existe sans ce marqueur, publier une nouvelle version
   au lieu de tenter de remplacer une distribution existante.
3. Installer `mcp-publisher` en suivant le
   [guide officiel](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/quickstart.mdx).
4. À la racine du dépôt, valider puis publier avec le compte GitHub
   `rmouahid` (authentification interactive) :

   ```bash
   mcp-publisher validate server.json
   mcp-publisher login github
   mcp-publisher publish server.json
   ```

5. Vérifier l'entrée renvoyée par l'API, son nom, sa version et son paquet :

   ```bash
   curl --fail 'https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.rmouahid/novit'
   ```

Une fois cette vérification réussie, ajouter au README un lien vers l'entrée
publique. Avant cela, conserver un lien vers cette procédure, sans badge
affirmant une publication.

Les règles de vérification du README sont décrites dans la
[documentation officielle des paquets PyPI](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/package-types.mdx#pypi-packages).
