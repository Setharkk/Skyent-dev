#!/usr/bin/env python
from app.db.session import async_engine
from app.db.base import Base
import asyncio
from sqlalchemy import inspect

async def show_tables():
    async with async_engine.connect() as conn:
        insp = inspect(conn)
        return await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

if __name__ == "__main__":
    tables = asyncio.run(show_tables())
    print("Tables in database:", tables)
