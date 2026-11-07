import sys
from pathlib import Path

from loguru import logger


def configure_logging(
    log_level: str = "INFO", log_dir: str = "", is_production: bool = False
) -> None:
    """Configure loguru selon l'environnement.

    En stdio MCP, les logs vont sur stderr uniquement —
    stdout est réservé au protocole JSON-RPC.
    """
    logger.remove()

    if is_production:
        # JSON structuré pour agrégation (Datadog, Loki, etc.)
        logger.add(
            sys.stderr,
            level=log_level,
            format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level} | {name}:{function}:{line} | {message}",
            serialize=True,
        )
    else:
        # Format lisible pour le développement
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — {message}",
            colorize=True,
        )

    if log_dir:
        log_path = Path(log_dir) / "novit.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_path),
            level=log_level,
            format="{time:YYYY-MM-DDTHH:mm:ss} | {level} | {name}:{line} | {message}",
            rotation="10 MB",
            retention="7 days",
            compression="gz",
            serialize=is_production,
        )
        logger.info(f"Logs fichier activés : {log_path}")
