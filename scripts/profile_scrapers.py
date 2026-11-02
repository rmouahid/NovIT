"""Mesure une collecte complète sur les sources réelles (#90).

Lance tous les scrapers comme le serveur (ScraperManager.fetch_all) et
affiche le temps total puis les sources les plus lentes :

    python scripts/profile_scrapers.py [--top 10]

Les scrapers tournent en parallèle : le temps total est celui de la source
la plus lente, plafonné par le timeout par scraper (30 s).
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger  # noqa: E402

from novit.scrapers.manager import ScraperManager  # noqa: E402


async def main(top: int) -> None:
    logger.remove()
    manager = ScraperManager()
    start = time.perf_counter()
    result = await manager.fetch_all()
    total = time.perf_counter() - start

    print(
        f"Collecte complète : {total:.1f} s · {len(manager._scrapers)} sources "
        f"({len(result.sources_ok)} OK, {len(result.sources_failed)} en échec) · "
        f"{len(result.articles)} articles uniques"
    )
    print(f"\n{'durée':>7}  {'état':5}  {'articles':>8}  source")
    for report in sorted(result.reports, key=lambda r: -r.duration_ms)[:top]:
        state = "OK" if report.success else "KO"
        print(
            f"{report.duration_ms / 1000:6.1f}s  {state:5}  {report.article_count:8}  "
            f"{report.scraper} {report.error[:60]}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--top", type=int, default=10, help="sources affichées")
    asyncio.run(main(parser.parse_args().top))
