#!/usr/bin/env python3
"""Seed the database with quality mock data for local testing / demos.

Creates all tables from the ORM models (if they don't exist) and inserts a
realistic dataset: several users, city thrift/vintage maps with shops, per-day
opening hours (including closed days and split shifts), and a few completed
purchases + invoices.

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
from src.python.app.models import Invoice, Location, LocationHours, Map, Purchase, User

SAMPLE_EMAIL = "test@example.com"
SAMPLE_PASSWORD = "password123"


# ─── hours helper ────────────────────────────────────────────────────────────

def build_hours(default=None, closed=(), overrides=None):
    """Build a week of LocationHours rows. (0 = Monday ... 6 = Sunday)

    default:   (open_hour, close_hour) applied to every non-closed, non-override day.
    closed:    iterable of day indices that are explicitly closed.
    overrides: dict day_index -> list of (open_hour, close_hour) tuples, for split shifts.
    """
    overrides = overrides or {}
    rows: list[LocationHours] = []
    for day in range(7):
        if day in closed:
            rows.append(LocationHours(day_of_week=day, is_closed=True))
        elif day in overrides:
            for open_h, close_h in overrides[day]:
                rows.append(
                    LocationHours(day_of_week=day, open_time=time(open_h, 0), close_time=time(close_h, 0))
                )
        elif default:
            rows.append(
                LocationHours(day_of_week=day, open_time=time(default[0], 0), close_time=time(default[1], 0))
            )
    return rows


# ─── dataset ─────────────────────────────────────────────────────────────────

USERS = [
    (SAMPLE_EMAIL, "Test", "User"),
    ("jane@example.com", "Jane", "Doe"),
    ("alex.rivera@example.com", "Alex", "Rivera"),
    ("sam.chen@example.com", "Sam", "Chen"),
    ("maria.gomez@example.com", "Maria", "Gomez"),
]

# Each map: dict with metadata + list of location dicts.
MAPS = [
    {
        "name": "Boston Thrift & Vintage Map",
        "slug": "boston-thrift",
        "region": "Boston, MA",
        "price": 1999,
        "description": "Hand-picked secondhand, vintage, and consignment shops across Boston and Cambridge.",
        "locations": [
            {
                "name": "Garment District",
                "latitude": 42.3631, "longitude": -71.0992,
                "min_price": 5, "max_price": 80, "price_level": 2,
                "description": "Two floors of vintage plus the legendary $2/lb 'Dollar a Pound' bins.",
                "hours": build_hours(default=(11, 19)),
            },
            {
                "name": "Boomerangs Special Edition",
                "latitude": 42.3493, "longitude": -71.0846,
                "min_price": 3, "max_price": 50, "price_level": 1,
                "description": "Nonprofit thrift benefiting AIDS Action Committee; curated designer finds.",
                "hours": build_hours(default=(10, 18), closed={0}),  # closed Mondays
            },
            {
                "name": "The Closet Inc.",
                "latitude": 42.3503, "longitude": -71.0810,
                "min_price": 15, "max_price": 250, "price_level": 3,
                "description": "Upscale consignment on Newbury St — designer labels at a fraction of retail.",
                "hours": build_hours(default=(11, 18), closed={6}),  # closed Sundays
            },
            {
                "name": "Goodwill Cambridge",
                "latitude": 42.3736, "longitude": -71.1097,
                "min_price": 2, "max_price": 40, "price_level": 1,
                "description": "Large-format thrift near Central Square; deep racks, frequent restocks.",
                "hours": build_hours(default=(9, 21)),
            },
        ],
    },
    {
        "name": "NYC Vintage Map",
        "slug": "nyc-vintage",
        "region": "New York, NY",
        "price": 2999,
        "description": "Curated vintage and resale spots across Manhattan and Brooklyn.",
        "locations": [
            {
                "name": "L Train Vintage",
                "latitude": 40.7193, "longitude": -73.9573,
                "min_price": 10, "max_price": 120, "price_level": 2,
                "description": "Williamsburg staple known for organized racks by color and decade.",
                "hours": build_hours(default=(12, 20)),
            },
            {
                "name": "Beacon's Closet (Greenpoint)",
                "latitude": 40.7300, "longitude": -73.9540,
                "min_price": 8, "max_price": 150, "price_level": 2,
                "description": "Buy-sell-trade powerhouse; designer and everyday pieces.",
                "hours": build_hours(default=(11, 20)),
            },
            {
                "name": "Housing Works Thrift (Chelsea)",
                "latitude": 40.7440, "longitude": -73.9960,
                "min_price": 5, "max_price": 200, "price_level": 2,
                "description": "Charity thrift with a great furniture and book selection.",
                "hours": build_hours(default=(10, 19), closed={6}),
            },
            {
                "name": "Buffalo Exchange (Williamsburg)",
                "latitude": 40.7142, "longitude": -73.9614,
                "min_price": 8, "max_price": 90, "price_level": 2,
                "description": "Trade your closet for cash or credit; trend-forward inventory.",
                "hours": build_hours(default=(11, 20)),
            },
        ],
    },
    {
        "name": "Los Angeles Thrift Map",
        "slug": "la-thrift",
        "region": "Los Angeles, CA",
        "price": 2499,
        "description": "Sun-soaked vintage warehouses and curated boutiques from Melrose to Echo Park.",
        "locations": [
            {
                "name": "Jet Rag",
                "latitude": 34.0830, "longitude": -118.3490,
                "min_price": 5, "max_price": 100, "price_level": 2,
                "description": "Famous Sunday $1 parking-lot sale; weekday vintage racks inside.",
                # split hours on Sunday: early $1 lot sale, then regular hours
                "hours": build_hours(default=(11, 19), overrides={6: [(7, 10), (11, 19)]}),
            },
            {
                "name": "Wasteland (Melrose)",
                "latitude": 34.0838, "longitude": -118.3610,
                "min_price": 15, "max_price": 200, "price_level": 3,
                "description": "Curated vintage and contemporary designer resale on Melrose Ave.",
                "hours": build_hours(default=(11, 20)),
            },
            {
                "name": "Crossroads Trading (Los Feliz)",
                "latitude": 34.0900, "longitude": -118.3270,
                "min_price": 8, "max_price": 120, "price_level": 2,
                "description": "Buy-sell-trade with a strong denim and outerwear selection.",
                "hours": build_hours(default=(11, 19), closed={0}),
            },
        ],
    },
    {
        "name": "Portland Vintage Map",
        "slug": "portland-vintage",
        "region": "Portland, OR",
        "price": 1799,
        "description": "Rain-or-shine thrift crawl through Hawthorne, Alberta, and downtown.",
        "locations": [
            {
                "name": "House of Vintage",
                "latitude": 45.5120, "longitude": -122.6190,
                "min_price": 6, "max_price": 90, "price_level": 2,
                "description": "13,000 sq ft of booths spanning every decade.",
                "hours": build_hours(default=(11, 19)),
            },
            {
                "name": "Red Light Clothing Exchange",
                "latitude": 45.5118, "longitude": -122.6200,
                "min_price": 10, "max_price": 110, "price_level": 2,
                "description": "Costume-worthy vintage and a sharp denim wall.",
                "hours": build_hours(default=(11, 19), closed={2}),  # closed Wednesdays
            },
            {
                "name": "Buffalo Exchange (Hawthorne)",
                "latitude": 45.5122, "longitude": -122.6210,
                "min_price": 8, "max_price": 80, "price_level": 1,
                "description": "Neighborhood trade shop with quick turnover.",
                "hours": build_hours(default=(11, 20)),
            },
        ],
    },
    {
        "name": "Chicago Thrift Map",
        "slug": "chicago-thrift",
        "region": "Chicago, IL",
        "price": 1999,
        "description": "Vintage and resale gems from Wicker Park to Andersonville.",
        "locations": [
            {
                "name": "Knee Deep Vintage",
                "latitude": 41.8540, "longitude": -87.6680,
                "min_price": 12, "max_price": 160, "price_level": 3,
                "description": "Pilsen institution for true antique and mid-century clothing.",
                "hours": build_hours(default=(12, 19), closed={1}),  # closed Tuesdays
            },
            {
                "name": "Brown Elephant (Andersonville)",
                "latitude": 41.9810, "longitude": -87.6690,
                "min_price": 3, "max_price": 75, "price_level": 1,
                "description": "Resale benefiting Howard Brown Health; huge, ever-changing stock.",
                "hours": build_hours(default=(11, 18)),
            },
            {
                "name": "Kokorokoko",
                "latitude": 41.9100, "longitude": -87.6770,
                "min_price": 15, "max_price": 140, "price_level": 3,
                "description": "'80s–'00s vintage specialists in Wicker Park.",
                "hours": build_hours(default=(12, 19), closed={1, 2}),  # closed Tue & Wed
            },
        ],
    },
]

# Completed purchases: (user_email, map_slug). An invoice + purchase is created for each.
PURCHASES = [
    (SAMPLE_EMAIL, "boston-thrift"),
    (SAMPLE_EMAIL, "nyc-vintage"),
    ("jane@example.com", "la-thrift"),
    ("alex.rivera@example.com", "portland-vintage"),
    ("sam.chen@example.com", "boston-thrift"),
]


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
        users = {
            email: User(
                email=email,
                first_name=first,
                last_name=last,
                hashed_password=hash_password(SAMPLE_PASSWORD),
            )
            for email, first, last in USERS
        }
        db.add_all(users.values())

        # Maps + locations (+ nested hours via relationship cascade)
        maps = {}
        loc_count = 0
        for m in MAPS:
            locations = []
            for loc in m["locations"]:
                locations.append(
                    Location(
                        name=loc["name"],
                        latitude=loc["latitude"],
                        longitude=loc["longitude"],
                        min_price=loc["min_price"],
                        max_price=loc["max_price"],
                        price_level=loc["price_level"],
                        description=loc["description"],
                        hours=loc["hours"],
                    )
                )
            loc_count += len(locations)
            maps[m["slug"]] = Map(
                name=m["name"],
                slug=m["slug"],
                region=m["region"],
                price=m["price"],
                description=m["description"],
                locations=locations,
            )
        db.add_all(maps.values())

        # Completed purchases + their invoices (linked via relationships)
        for i, (email, slug) in enumerate(PURCHASES, start=1):
            user = users[email]
            mp = maps[slug]
            invoice = Invoice(
                user=user,
                map=mp,
                stripe_checkout_session_id=f"cs_test_seed_{i:04d}",
                stripe_payment_intent_id=f"pi_test_seed_{i:04d}",
                stripe_customer_id=f"cus_seed_{email.split('@')[0]}",
                amount=mp.price,
                currency="usd",
                status="paid",
            )
            db.add(invoice)
            db.add(Purchase(user=user, map=mp, invoice=invoice))

        await db.commit()

        print(
            f"Seeded:\n"
            f"  users:     {len(users)}\n"
            f"  maps:      {len(maps)}\n"
            f"  locations: {loc_count} (with per-day hours)\n"
            f"  purchases: {len(PURCHASES)} (+ matching paid invoices)\n"
            f"  Login with: {SAMPLE_EMAIL} / {SAMPLE_PASSWORD}"
        )

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed quality mock data for local testing.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables before seeding (destroys existing data).",
    )
    args = parser.parse_args()
    asyncio.run(seed(args.reset))
