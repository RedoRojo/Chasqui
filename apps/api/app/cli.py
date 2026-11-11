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
        print(f"[Chasqui] Starting live scan across Bolivian news sources (live={live})...")
        run = run_daily_scan(
            db,
            trigger="cli",
            try_live_network=live,
            max_per_source=max_per_source,
        )
        print(
            f"[Chasqui] Scan finished ({run.status}): "
            f"{run.sources_scanned} sources scanned | "
            f"+{run.new_articles} new articles | "
            f"+{run.new_events} new events | "
            f"{run.updated_threads} threads updated."
        )
    finally:
        db.close()


def cmd_seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        print("[Chasqui] Initializing source catalog, historical baseline, and live scan...")
        seed_database(db, run_live_after_seed=True)
        ov = get_overview(db)
        print(
            f"[Chasqui] Ready: {ov.total_sources} sources | "
            f"{ov.total_threads} threads | {ov.total_events} events | "
            f"{ov.total_articles} articles."
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
        print("=== CHASQUI DATABASE STATUS ===")
        print(f"Active sources      : {ov.total_sources}")
        print(f"Tracked threads     : {ov.total_threads}")
        print(f"Chronological events: {ov.total_events}")
        print(f"Archived articles   : {ov.total_articles}")
        print(f"Blindspot events    : {ov.blindspot_events_count}")
        print(f"Non-mainstream share: {ov.alternative_coverage_share}%")
        print("\n=== TOP EVOLVING STORY THREADS ===")
        for th in threads[:10]:
            print(
                f" - [{th.primary_department} | {th.category}] {th.title[:70]} "
                f"({th.events_count} milestones, {th.articles_count} articles)"
            )
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Chasqui CLI for daily scanning and database management",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Run a live scan across all active Bolivian news sources")
    scan_p.add_argument(
        "--max-per-source",
        type=int,
        default=4,
        help="Maximum new articles to ingest per source in this run (default: 4)",
    )

    sub.add_parser("seed", help="Initialize source catalog, historical baseline, and initial scan")
    sub.add_parser("status", help="Display current database summary and top story threads")

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
