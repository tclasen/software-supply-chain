from typing import Annotated

import logfire
from sqlalchemy import JSON, func
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import Column, Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession


class Package(SQLModel, table=True):
    name: Annotated[str, Field(primary_key=True)]
    last_serial: int
    dependencies: list[str] = Field(sa_column=Column(JSON), default_factory=list)


deps_func = func.json_each(Package.dependencies).table_valued("value", joins_implicitly=True)

engine = create_async_engine("sqlite+aiosqlite:///pypi.db", connect_args={"autocommit": False})

logfire.configure()
logfire.instrument_sqlalchemy(engine=engine)


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_packages(
    session: AsyncSession,
    limit: int = 10,
    offset: int = 0,
    package_name: str | None = None,
) -> list[Package]:
    statement = select(Package)
    if package_name:
        statement = statement.filter(deps_func.c.value == package_name)
    statement = statement.limit(limit).offset(offset)
    query = await session.exec(statement)
    results = query.all()
    return list(results)
