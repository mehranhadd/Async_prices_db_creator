"""Asynchronous SQLite persistence."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import aiosqlite

from .config import get_database_path

CREATE_TABLE_SQL = """CREATE TABLE IF NOT EXISTS mobiles (
    name TEXT PRIMARY KEY,
    price TEXT
)"""
INSERT_SQL = "INSERT INTO mobiles(name, price) VALUES(?, ?)"
SELECT_SQL = "SELECT name, price FROM mobiles"


def _prepare_database_path(path: str | os.PathLike[str] | None) -> Path:
    database_path = get_database_path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return database_path


async def initialize_database(
    db_path: str | os.PathLike[str] | None = None,
) -> Path:
    """Create the database file and existing ``mobiles`` schema if necessary."""
    path = _prepare_database_path(db_path)
    async with aiosqlite.connect(str(path)) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()
    return path


async def save_products(
    products: Iterable[tuple[str, str]],
    db_path: str | os.PathLike[str] | None = None,
) -> int:
    """Insert product name/price pairs asynchronously and return count.

    Call :func:`initialize_database` before this function so the ``mobiles``
    table exists. The table schema and plain INSERT semantics are preserved.
    One connection is reused, and each successful row is committed before the
    next one.
    """
    path = _prepare_database_path(db_path)
    inserted = 0
    async with aiosqlite.connect(str(path)) as db:
        for product in products:
            await db.execute(INSERT_SQL, product)
            await db.commit()
            inserted += 1
    return inserted


async def read_products(
    db_path: str | os.PathLike[str] | None = None,
) -> list[tuple[str, str]]:
    """Return all saved rows in the same order SQLite currently returns them."""
    path = get_database_path(db_path)
    async with aiosqlite.connect(str(path)) as db:
        async with db.execute(SELECT_SQL) as cursor:
            return await cursor.fetchall()
