"""Block until the database accepts connections, then exit 0.

Used by the Compose ``migrate`` service so migrations don't race Postgres boot.
"""
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


async def wait(timeout: float = 60.0, interval: float = 1.5) -> None:
    engine = create_async_engine(settings.database_url)
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            print("Database is ready.")
            return
        except Exception as exc:  # noqa: BLE001
            if asyncio.get_event_loop().time() > deadline:
                print(f"Database not ready after {timeout}s: {exc}", file=sys.stderr)
                sys.exit(1)
            print("Waiting for database...")
            await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(wait())
