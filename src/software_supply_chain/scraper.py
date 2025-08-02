import re
from typing import Annotated

import httpx
import logfire
from httpx_retries import Retry, RetryTransport
from pydantic import AfterValidator, BeforeValidator, ConfigDict, Field
from pydantic import BaseModel as PydanticBaseModel

logfire.instrument_httpx()

retry = Retry(total=5, backoff_factor=0.5)
transport = RetryTransport(retry=retry)


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(extra="ignore")


class PackageOverview(BaseModel):
    name: str
    last_serial: Annotated[int, Field(alias="_last-serial")]


class PackageListMeta(BaseModel):
    api_version: Annotated[str, Field(alias="api-version")]
    last_serial: Annotated[int, Field(alias="_last-serial")]


class PackageList(BaseModel):
    meta: PackageListMeta
    projects: tuple[PackageOverview, ...]


async def list_all_packages() -> PackageList:
    async with httpx.AsyncClient(
        transport=transport,
        headers={"Accept": "application/vnd.pypi.simple.v1+json"},
    ) as client:
        response = await client.get("https://pypi.org/simple/")
    response.raise_for_status()
    return PackageList.model_validate_json(response.text)


def strip_package_version(string: str) -> str:
    results = re.split(r"[\[;,<>=!~\s]+", string)
    return normalize(results[0])


def normalize(string: str) -> str:
    return re.sub(r"[-_.]+", "-", string).lower()


class PackageInfo(BaseModel):
    name: Annotated[str, AfterValidator(normalize)]
    requires_dist: set[Annotated[str, BeforeValidator(strip_package_version)]] | None


class Package(BaseModel):
    info: PackageInfo
    last_serial: int


async def get_package_metadata(package_name: str) -> Package | None:
    async with httpx.AsyncClient(transport=transport, headers={"Accept": "application/json"}) as client:
        response = await client.get(f"https://pypi.org/pypi/{package_name}/json")
    if response.is_error:
        return None
    return Package.model_validate_json(response.text)
