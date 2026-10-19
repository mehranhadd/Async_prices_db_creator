from __future__ import annotations

import asyncio
import sqlite3

import pytest

pytest.importorskip("aiosqlite")

from async_prices_db_creator.database import initialize_database, read_products, save_products


def test_initialize_and_save_products(tmp_path):
    path = tmp_path / "nested" / "Phone_prices.db"
    asyncio.run(initialize_database(path))
    inserted = asyncio.run(save_products([("Phone A", "100"), ("Phone B", "200")], path))
    assert inserted == 2
    assert asyncio.run(read_products(path)) == [("Phone A", "100"), ("Phone B", "200")]


def test_schema_is_preserved(tmp_path):
    path = asyncio.run(initialize_database(tmp_path / "Phone_prices.db"))

    async def read_schema():
        import aiosqlite
        async with aiosqlite.connect(str(path)) as db:
            async with db.execute("PRAGMA table_info(mobiles)") as cursor:
                return await cursor.fetchall()

    columns = asyncio.run(read_schema())
    assert [(col[1], col[2], col[5]) for col in columns] == [
        ("name", "TEXT", 1),
        ("price", "TEXT", 0),
    ]


def test_duplicate_name_raises_and_keeps_prior_committed_row(tmp_path):
    path = tmp_path / "Phone_prices.db"
    asyncio.run(initialize_database(path))
    with pytest.raises(sqlite3.IntegrityError):
        asyncio.run(save_products([("Phone A", "100"), ("Phone A", "999")], path))
    assert asyncio.run(read_products(path)) == [("Phone A", "100")]
