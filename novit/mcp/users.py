"""Utilisateurs d'une instance partagée (#87).

En HTTP, chaque utilisateur reçoit son propre jeton (`NOVIT_API_TOKENS`) :
le middleware d'authentification en déduit l'identifiant, que `call_tool`
place dans `current_user` le temps de l'appel. Préférences et sessions sont
rangées sous cet identifiant, si bien qu'un utilisateur ne voit jamais celles
d'un autre.

En stdio, ou avec le jeton unique `NOVIT_API_TOKEN`, tout se fait sous
l'utilisateur `default` : le fonctionnement mono-utilisateur est inchangé.
"""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

DEFAULT_USER = "default"

# Sert de nom de fichier : pas de séparateur de chemin, pas de « .. ».
USER_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")

current_user: ContextVar[str] = ContextVar("novit_user", default=DEFAULT_USER)


def parse_api_tokens(raw: str) -> dict[str, str]:
    """Lit `NOVIT_API_TOKENS` (« alice:jeton1,bob:jeton2 ») en {jeton: utilisateur}."""
    tokens: dict[str, str] = {}
    users: set[str] = set()
    for entry in filter(None, (part.strip() for part in raw.split(","))):
        user, sep, token = entry.partition(":")
        user, token = user.strip(), token.strip()
        if not sep or not token:
            raise ValueError(f"NOVIT_API_TOKENS : entrée « {user} » sans jeton")
        if not USER_ID.fullmatch(user):
            raise ValueError(
                f"NOVIT_API_TOKENS : identifiant « {user} » invalide "
                "(minuscules, chiffres, _ et -, 32 caractères au plus)"
            )
        if user in users:
            raise ValueError(f"NOVIT_API_TOKENS : utilisateur « {user} » en double")
        if token in tokens:
            raise ValueError(
                "NOVIT_API_TOKENS : un même jeton sert à deux utilisateurs"
            )
        users.add(user)
        tokens[token] = user
    return tokens


@contextmanager
def as_user(user: str) -> Iterator[None]:
    """Exécute le bloc sous l'identité `user`."""
    reset = current_user.set(user)
    try:
        yield
    finally:
        current_user.reset(reset)
