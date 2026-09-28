"""Session de démonstration NovIT, sans client MCP graphique.

Lance le serveur NovIT en stdio, comme le ferait un client MCP, appelle
quelques outils sur les sources en direct et affiche leurs réponses.

    python scripts/demo.py                       # scénario par défaut
    python scripts/demo.py --json session.json   # enregistre aussi la session

Utile pour vérifier une installation ou montrer NovIT en action : c'est ce
script qui a produit la démo du README.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent

# (outil, arguments) appelés dans l'ordre
SCENARIO = [
    ("novit_start", {"profil": "INGENIEUR"}),
    (
        "novit_get_news",
        {"profil": "INGENIEUR", "domaines": ["ia"], "nb_articles": 3, "periode": "7j"},
    ),
    ("novit_search", {"query": "agents", "per_page": 3}),
]


async def run(scenario: list[tuple[str, dict]]) -> list[dict]:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "src.mcp"], cwd=str(ROOT)
    )
    transcript = []
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"NovIT connecté · {len(tools.tools)} outils MCP disponibles\n")

            for name, arguments in scenario:
                print(f"▶ {name} {json.dumps(arguments, ensure_ascii=False)}")
                start = time.monotonic()
                result = await session.call_tool(name, arguments)
                elapsed = time.monotonic() - start
                text = "\n".join(
                    block.text for block in result.content if hasattr(block, "text")
                )
                print(f"{text}\n({elapsed:.1f} s)\n")
                transcript.append(
                    {
                        "tool": name,
                        "arguments": arguments,
                        "seconds": round(elapsed, 1),
                        "response": text,
                    }
                )
    return transcript


def main() -> None:
    parser = argparse.ArgumentParser(description="Session de démonstration NovIT")
    parser.add_argument("--json", type=Path, help="enregistre la session en JSON")
    args = parser.parse_args()

    transcript = asyncio.run(run(SCENARIO))
    if args.json:
        args.json.write_text(
            json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
