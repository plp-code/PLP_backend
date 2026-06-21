#!/usr/bin/env python3
"""Seed the database with mock data for local testing.

Creates all tables from the ORM models (if they don't exist) and inserts a few
sample users, maps, and locations. Safe to re-run: it skips seeding if the
sample data is already present.

Usage (run from the repo root, with the venv active):
    python scripts/seed_data.py            # create tables + insert sample data
    python scripts/seed_data.py --reset    # DROP all tables first, then reseed

Honors whatever DATABASE_URL is in your .env (MySQL, SQLite, etc.).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import time

# Make `src.python.app...` importable when run as `python scripts/seed_data.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from src.python.app.core.database import AsyncSessionLocal, Base, engine
from src.python.app.core.security import hash_password
from src.python.app import models  # noqa: F401  (registers every table on Base.metadata)
from src.python.app.models import Location, LocationHours, Map, User


def weekday_hours(open_h: int, close_h: int, closed_days: set[int] | None = None):
    """Build a week of LocationHours: open_h-close_h Mon-Sun, closed on closed_days."""
    closed_days = closed_days or set()
    rows = []
    for day in range(7):  # 0 = Monday ... 6 = Sunday
        if day in closed_days:
            rows.append(LocationHours(day_of_week=day, is_closed=True))
        else:
            rows.append(
                LocationHours(day_of_week=day, open_time=time(open_h, 0), close_time=time(close_h, 0))
            )
    return rows

SAMPLE_EMAIL = "test@example.com"
SAMPLE_PASSWORD = "password123"


async def seed(reset: bool) -> None:
    async with engine.begin() as conn:
        if reset:
            print("Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
        print("Creating tables (if missing)...")
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == SAMPLE_EMAIL))
        if existing:
            print("Sample data already present — nothing to do. (use --reset to rebuild)")
            await engine.dispose()
            return

        # Users
        users = [
            User(
                email=SAMPLE_EMAIL,
                first_name="Test",
                last_name="User",
                hashed_password=hash_password(SAMPLE_PASSWORD),
            ),
            User(
                email="jane@example.com",
                first_name="Jane",
                last_name="Doe",
                hashed_password=hash_password(SAMPLE_PASSWORD),
            ),
        ]
        db.add_all(users)

        # Maps with nested locations (relationship cascade inserts the locations)
        boston = Map(
            name="Boston Thrift Map",
            slug="boston-thrift",
            region="Boston, MA",
            price=1999,
            description="Hand-picked secondhand and vintage shops around Boston.",
            locations=[
                Location(
                    name="Garment District",
                    latitude=42.3631,
                    longitude=-71.0992,
                    min_price=5,
                    max_price=80,
                    price_level=2,
                    hours=weekday_hours(11, 19),  # open every day 11:00-19:00
                ),
                Location(
                    name="Boomerangs Special Edition",
                    latitude=42.3493,
                    longitude=-71.0846,
                    min_price=3,
                    max_price=50,
                    price_level=1,
                    hours=weekday_hours(10, 18, closed_days={0}),  # closed Mondays
                ),
            ],
        )
        nyc = Map(
            name="NYC Vintage Map",
            slug="nyc-vintage",
            region="New York, NY",
            price=2999,
            description="Curated vintage spots across Manhattan and Brooklyn.",
            locations=[
                Location(
                    name="L Train Vintage",
                    latitude=40.7193,
                    longitude=-73.9573,
                    min_price=10,
                    max_price=120,
                    price_level=2,
                    hours=weekday_hours(12, 20, closed_days={1, 2}),  # closed Tue & Wed
                ),
            ],
        )
        db.add_all([boston, nyc])

        await db.commit()
        print(
            f"Seeded {len(users)} users and 2 maps with locations.\n"
            f"  Login with: {SAMPLE_EMAIL} / {SAMPLE_PASSWORD}"
        )

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed mock data for local testing.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables before seeding (destroys existing data).",
    )
    args = parser.parse_args()
    asyncio.run(seed(args.reset))
