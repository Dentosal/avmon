"""A simple visualization front-end."""

from typing import AsyncIterator, List, Union

import datetime
import urllib.parse
import asyncio
from aiohttp import web

from . import postgres
from . import config


routes = web.RouteTableDef()

HEADERS = {"Cache-Control": "no-cache"}

with open("avmon/frontend.html") as f:
    HTML_TEMPLATE = f.read()


def make_html(body):
    return HTML_TEMPLATE.replace("$CONTENT", body)


class HtmlTag:
    def __init__(
        self,
        tag: str,
        contents: Union["HtmlTag", str, List[Union["HtmlTag", str]]] = [],
        **kwargs,
    ) -> None:
        self.tag = tag
        self.args = kwargs
        self.args["class"] = self.args.get("classes_", [])
        self.contents = contents[:] if isinstance(contents, list) else [contents]

    def append(self, value: Union[str, "HtmlTag"]) -> None:
        self.contents.append(value)

    @property
    def classes(self) -> List[str]:
        return self.args["class"]  # type: ignore

    @property
    def html(self) -> str:
        result = f"<{self.tag}"
        for key, value in self.args.items():
            if isinstance(value, list):
                value = " ".join(value)
            assert '"' not in value
            result += " " + key + '="' + value + '"'
        result += f">"
        for c in self.contents:
            if isinstance(c, str):
                result += c
            else:
                assert isinstance(c, HtmlTag), f"{c !r}"
                result += c.html
        result += f"</{self.tag}>"
        return result


def make_table(columns: List[str]) -> HtmlTag:
    table = HtmlTag("table")
    thead = HtmlTag("thead")
    for c in columns:
        thead.contents.append(HtmlTag("th", contents=c))
    table.contents.append(thead)
    return table


@routes.get("/")
async def all(request: web.Request) -> web.Response:
    async with request.config_dict["DB"].acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT ON (url) url, reached, error, status, time_start, (time_end - time_start) as delay
            FROM status_history
            ORDER BY url ASC, time_start DESC
            """
        )

    table = make_table(
        ["Endpoint", "Reached", "Status", "Time (UTC)", "Delay", "History"]
    )
    for row in rows:
        tr = HtmlTag("tr")

        if not row["reached"]:
            tr.classes.append("unreachable")

        tr.append(
            HtmlTag(
                "td",
                contents=HtmlTag("a", contents=row["url"], href=row["url"]),
            )
        )

        tr.append(HtmlTag("td", contents=str(row["reached"]), classes=["reached"]))

        status_cell = HtmlTag("td")
        if row["reached"]:
            status_cell.contents = [str(row["status"])]
            status_cell = HtmlTag("td", contents=str(row["status"]))
            if 200 <= row["status"] < 300:
                status_cell.classes.append("ok")
            elif 400 <= row["status"] < 600:
                status_cell.classes.append("error")
        else:
            status_cell.contents = [row["error"]]
            status_cell.classes.append("error")
        tr.append(status_cell)

        tr.append(HtmlTag("td", contents=str(row["time_start"])))
        tr.append(HtmlTag("td", contents=f"{row['delay'].seconds:.2f}"))

        tr.append(
            HtmlTag(
                "td",
                contents=HtmlTag(
                    "a",
                    contents="Show history",
                    href=urllib.parse.quote_plus(row["url"]),
                ),
            )
        )

        table.contents.append(tr)

    return web.Response(
        text=make_html("<h1>Endpoint status</h1>" + table.html),
        content_type="text/html",
        headers=HEADERS,
    )


@routes.get("/{url}")
async def single(request: web.Request) -> web.Response:
    url = request.match_info.get("url")
    assert url
    limit = max(1, int(request.query.get("limit", 10)))

    async with request.config_dict["DB"].acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT reached, error, status, time_start, (time_end - time_start) as delay
            FROM status_history
            WHERE url = $1
            ORDER BY time_start DESC
            LIMIT $2
            """,
            url,
            limit,
        )

    table = make_table(["Reached", "Status", "Time (UTC)", "Delay"])

    for row in rows:
        tr = HtmlTag("tr")

        if not row["reached"]:
            tr.classes.append("unreachable")

        tr.append(HtmlTag("td", contents=str(row["reached"]), classes=["reached"]))

        status_cell = HtmlTag("td")
        if row["reached"]:
            status_cell.contents = [str(row["status"])]
            status_cell = HtmlTag("td", contents=str(row["status"]))
            if 200 <= row["status"] < 300:
                status_cell.classes.append("ok")
            elif 400 <= row["status"] < 600:
                status_cell.classes.append("error")
        else:
            status_cell.contents = [row["error"]]
            status_cell.classes.append("error")
        tr.append(status_cell)

        tr.append(HtmlTag("td", contents=str(row["time_start"])))
        tr.append(HtmlTag("td", contents=f"{row['delay'].seconds:.2f}"))

        table.contents.append(tr)

    link = HtmlTag("a", contents=url, href=url)
    prefix = f'<a href="/">Back to the front page</a><h1>History for {link.html}</h1>'
    suffix = ""
    if len(rows) == limit:
        suffix += f"<p>Showing first {limit} entries. "
        suffix += '<a href="?limit=' + str(limit + 10) + '">Show more</a>'
        suffix += "</p>"

    return web.Response(
        text=make_html(prefix + table.html + suffix),
        content_type="text/html",
        headers=HEADERS,
    )


def init_app() -> web.Application:
    config.load_dotenv()
    app = web.Application()
    app.add_routes(routes)
    app.cleanup_ctx.append(init_db)
    return app


async def init_db(app: web.Application) -> AsyncIterator[None]:
    db = await postgres.create_pool()
    app["DB"] = db
    yield
    await db.close()


async def main():
    runner = web.AppRunner(init_app())
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    await asyncio.Event().wait()  # forever


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
