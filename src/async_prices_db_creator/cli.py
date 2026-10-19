"""Command-line entry point."""

from __future__ import annotations

import argparse
import asyncio
import sqlite3
from pathlib import Path

import requests

from .config import BASE_URL, REQUEST_TIMEOUT_SECONDS, get_database_path
from .database import initialize_database, read_products, save_products
from .scraper import collect_products


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Collect mobile-phone names and prices from Technolife and save "
            "them to a SQLite database."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="SQLite database path (default: data/Phone_prices.db in the project).",
    )
    parser.add_argument(
        "--home-url",
        default=None,
        help="Override the homepage URL (defaults to TECHNOLIFE_BASE_URL or the configured default).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=REQUEST_TIMEOUT_SECONDS,
        help=f"HTTP request timeout in seconds (default: {REQUEST_TIMEOUT_SECONDS:g}).",
    )
    parser.add_argument(
        "--no-print-rows",
        action="store_true",
        help="Do not print all rows after the database is updated.",
    )
    return parser


async def run(args: argparse.Namespace) -> int:
    database_path = get_database_path(args.database)
    products = collect_products(
        home_url=args.home_url or BASE_URL, timeout=args.timeout
    )
    # Explicitly create the database/schema before inserting any products.
    await initialize_database(database_path)
    inserted = await save_products(products, db_path=database_path)
    print(f"Inserted {inserted} product rows into {database_path}")

    if not args.no_print_rows:
        for row in await read_products(database_path):
            print(row)
    return inserted


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except (
        LookupError,
        OSError,
        ValueError,
        requests.RequestException,
        sqlite3.Error,
    ) as exc:
        parser.exit(status=1, message=f"error: {exc}\n")


if __name__ == "__main__":
    main()
