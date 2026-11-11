import argparse
import sys

from app.database import SessionLocal, init_db
from app.main import get_overview, list_threads
from app.scraper.engine import run_daily_scan
from app.seed import seed_database


def cmd_scan(live: bool = True, max_per_source: int = 4) -> None:
    init_db()
    db = SessionLocal()
    try:
        print(f"[Chasqui] Iniciando escaneo de fuentes bolivianas (live={live})...")
        run = run_daily_scan(
            db,
            trigger="cli",
            try_live_network=live,
            max_per_source=max_per_source,
        )
        print(
            f"[Chasqui] Escaneo finalizado ({run.status}): "
            f"{run.sources_scanned} fuentes revisadas | "
            f"+{run.new_articles} artículos nuevos | "
            f"+{run.new_events} eventos creados | "
            f"{run.updated_threads} hilos actualizados."
        )
    finally:
        db.close()


def cmd_seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        print("[Chasqui] Inicializando catálogo de fuentes, base histórica y escaneo en vivo...")
        seed_database(db, run_live_after_seed=True)
        ov = get_overview(db)
        print(
            f"[Chasqui] Listo: {ov.total_sources} fuentes | "
            f"{ov.total_threads} hilos | {ov.total_events} eventos | "
            f"{ov.total_articles} artículos."
        )
    finally:
        db.close()


def cmd_status() -> None:
    init_db()
    db = SessionLocal()
    try:
        ov = get_overview(db)
        threads = list_threads(
            department=None,
            category=None,
            status=None,
            blindspot_only=False,
            q=None,
            db=db,
        )
        print("=== ESTADO ACTUAL DE CHASQUI ===")
        print(f"Fuentes activas      : {ov.total_sources}")
        print(f"Hilos en seguimiento : {ov.total_threads}")
        print(f"Eventos cronológicos : {ov.total_events}")
        print(f"Artículos archivados : {ov.total_articles}")
        print(f"Eventos punto ciego  : {ov.blindspot_events_count}")
        print(f"Cobertura no masiva  : {ov.alternative_coverage_share}%")
        print("\n=== PRINCIPALES HILOS EN EVOLUCIÓN ===")
        for th in threads[:10]:
            print(
                f" - [{th.primary_department} | {th.category}] {th.title[:70]} "
                f"({th.events_count} hitos, {th.articles_count} notas)"
            )
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="CLI de gestión y escaneo diario de Chasqui",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Ejecutar escaneo en vivo de las fuentes bolivianas")
    scan_p.add_argument(
        "--max-per-source",
        type=int,
        default=4,
        help="Máximo de artículos nuevos por fuente en esta corrida (default: 4)",
    )

    sub.add_parser("seed", help="Inicializar catálogo, semilla histórica y escaneo inicial")
    sub.add_parser("status", help="Mostrar resumen actual de la base de datos de Chasqui")

    args = parser.parse_args()
    if args.command == "scan":
        cmd_scan(live=True, max_per_source=args.max_per_source)
    elif args.command == "seed":
        cmd_seed()
    elif args.command == "status":
        cmd_status()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
