"""Rapport des retours utilisateurs enregistrés par `novit_feedback` (#89).

    python scripts/feedback_report.py [--days 7] [--db ./novit.db] [--output rapport.md]

À lancer chaque semaine (cron, tâche planifiée) : le rapport liste les volumes
par type, les outils les plus cités, les bugs avec leur lien d'issue
pré-remplie, puis tous les commentaires de la période.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from novit.mcp.feedback import FeedbackStore, weekly_report  # noqa: E402


async def main(days: int, db: str | None, output: str | None) -> None:
    entries = await FeedbackStore(db).since(days)
    report = weekly_report(entries, days=days)
    if output:
        Path(output).write_text(report + "\n", encoding="utf-8")
        print(f"Rapport écrit dans {output} ({len(entries)} retour(s))")
    else:
        print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=7, help="période couverte")
    parser.add_argument("--db", help="base SQLite (défaut : NOVIT_DB_PATH)")
    parser.add_argument("--output", help="fichier Markdown à écrire")
    args = parser.parse_args()
    asyncio.run(main(args.days, args.db, args.output))
