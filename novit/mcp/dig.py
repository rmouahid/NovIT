import re

import httpx
from bs4 import BeautifulSoup
from loguru import logger

_BOILERPLATE_TAGS = {
    "nav",
    "footer",
    "header",
    "aside",
    "script",
    "style",
    "noscript",
    "form",
    "button",
}
_CONTENT_TAGS = {"article", "main", "section"}


def _extract_text(html: str) -> str:
    """Extrait le texte principal d'une page HTML (heuristique readability simplifiée)."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(_BOILERPLATE_TAGS):
        tag.decompose()

    # Chercher un bloc article/main/section en priorité
    for selector in _CONTENT_TAGS:
        block = soup.find(selector)
        if block:
            text = block.get_text(separator="\n", strip=True)
            if len(text) > 200:
                return text

    # Fallback : body complet
    body = soup.find("body")
    return (
        body.get_text(separator="\n", strip=True)
        if body
        else soup.get_text(separator="\n", strip=True)
    )


def _clean(text: str, max_chars: int = 4000) -> str:
    """Nettoie et tronque le texte extrait."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    lines = [line for line in text.splitlines() if len(line.strip()) > 20]
    clean = "\n".join(lines)
    if len(clean) > max_chars:
        clean = clean[:max_chars] + "\n\n[... article tronqué à 4000 caractères]"
    return clean


async def dig_url(url: str) -> str:
    """Récupère une URL et retourne le contenu textuel principal.

    Retourne un bloc markdown prêt à être transmis à Claude.
    """
    logger.debug(f"[dig] Récupération : {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            content_type = r.headers.get("content-type", "")
            if "text/html" not in content_type:
                return f"Ce lien pointe vers un fichier non-HTML ({content_type}). Impossible d'extraire le texte."
            html = r.text
    except httpx.TimeoutException:
        return f"Impossible de récupérer l'article : timeout (URL : {url})"
    except httpx.HTTPStatusError as e:
        return f"Erreur HTTP {e.response.status_code} lors de la récupération de {url}"
    except Exception as e:
        return f"Erreur inattendue lors de la récupération : {e}"

    raw_text = _extract_text(html)
    clean_text = _clean(raw_text)

    if len(clean_text) < 100:
        return f"Le contenu de cette page est trop court ou inaccessible (peut-être derrière un paywall).\nURL : {url}"

    return f"# Contenu extrait\n**Source :** {url}\n\n{clean_text}"
