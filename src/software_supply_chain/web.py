from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated

import logfire
from fastapi import Depends, FastAPI, Query
from fastapi.responses import HTMLResponse
from htmy import Component, Context, Renderer, html
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from software_supply_chain.db import engine, get_packages, init_db


def get_engine() -> AsyncEngine:
    return engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    engine = get_engine()
    await init_db(engine)
    yield


app = FastAPI(lifespan=lifespan)
logfire.configure()
logfire.instrument_fastapi(app)


async def get_session(engine: Annotated[AsyncEngine, Depends(get_engine)]) -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(engine) as session:
        yield session


class Package(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    dependencies: list[str]


class PackageList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    packages: list[Package]


@dataclass
class PackagePage:
    package_list: PackageList
    limit: int
    offset: int
    search: str | None = None

    def htmy(self, _: Context) -> Component:
        page = (self.offset // self.limit) + 1
        pages_to_display = 9
        min_page = max(1, page - (pages_to_display // 2))
        max_page = min_page + pages_to_display
        search = f"&search={self.search}" if self.search else ""
        buttons = [
            link_button(
                str(i),
                i == page,
                f"/?limit={self.limit}&offset={((i - 1) * self.limit)}{search}",
            )
            for i in range(min_page, max_page)
        ]
        return (
            html.DOCTYPE.html,
            html.html(
                html.head(
                    html.title("Software Supply Chain"),
                    html.meta.charset(),
                    html.meta.viewport(),
                    html.link(
                        rel="stylesheet",
                        href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css",
                    ),
                    html.style("""
                    :root {
                        --pico-typography-spacing-vertical: 0.5rem;
                        --pico-form-element-spacing-vertical: 0rem;
                        --pico-form-element-spacing-horizontal: 0.25rem;
                    }
                    """),
                ),
                html.body(
                    html.main(
                        html.form(
                            html.input_(name="search", type="search", placeholder="Search...", value=self.search),
                            html.input_(type="submit", value="Search"),
                            role="search",
                        ),
                        html.table(
                            html.thead(
                                html.tr(
                                    html.td("Package"),
                                    html.td("Dependencies"),
                                ),
                            ),
                            *[
                                html.tr(
                                    html.td(
                                        link_button(
                                            package.name,
                                            False,  # noqa: FBT003
                                            f"/?search={package.name}",
                                        )
                                    ),
                                    html.td(
                                        html.ul(
                                            *[
                                                link_button(
                                                    dep,
                                                    False,  # noqa: FBT003
                                                    f"/?search={dep}",
                                                )
                                                for dep in sorted(package.dependencies)
                                            ],
                                        ),
                                    ),
                                )
                                for package in self.package_list.packages
                            ],
                            class_="striped",
                        ),
                        html.div(
                            *buttons,
                            role="group",
                        ),
                        class_="container",
                    ),
                ),
            ),
        )


def link_button(text: str, current: bool, url: str) -> html.a:  # noqa: FBT001
    attrs = {}
    if current:
        attrs["aria-current"] = "true"
    return html.a(text, role="button", href=url, **attrs)


@app.get("/", response_class=HTMLResponse)
async def index(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: str | None = None,
) -> HTMLResponse:
    packages = await get_packages(session, limit, offset, search)
    package_list = PackageList.model_validate({"packages": packages})
    content = await Renderer().render(PackagePage(package_list, limit, offset, search))
    return HTMLResponse(content=content)
