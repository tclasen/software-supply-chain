import logfire
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from software_supply_chain.db import Package, engine, init_db
from software_supply_chain.scraper import get_package_metadata, list_all_packages

logfire.configure()


async def package_is_updated(package_name: str, last_serial: int) -> bool:
    async with AsyncSession(engine) as session:
        statement = select(Package).where(Package.name == package_name)
        query = await session.exec(statement)
        result = query.one_or_none()
    return (result is not None) and (result.last_serial >= last_serial)


async def main() -> None:
    await init_db(engine)
    async with AsyncSession(engine) as session:
        packages = await list_all_packages()
        for package_info in packages.projects:
            if await package_is_updated(package_info.name, package_info.last_serial):
                continue

            package = await get_package_metadata(package_info.name)
            if package is None:
                continue

            model = Package(
                name=package.info.name,
                last_serial=package.last_serial,
                dependencies=sorted(package.info.requires_dist) if package.info.requires_dist else (),
            )
            await session.merge(model)
            await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
