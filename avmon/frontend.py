"""A simple visualization front-end."""

from typing import AsyncIterator

import datetime
import urllib.parse
import asyncio
from aiohttp import web

from . import postgres
from . import config


routes = web.RouteTableDef()


def make_html(body):
    with open("avmon/frontend.html") as f:
        HTML_TEMPLATE = f.read()
    return HTML_TEMPLATE.replace("$CONTENT", body)


@routes.get("/")
async def all(request: web.Request) -> web.Response:
    conn = request.config_dict["DB"]
    rows = await conn.fetch(
        """
        SELECT DISTINCT ON (url) url, reached, error, status, time_start, (time_end - time_start) as delay
        FROM status_history
        ORDER BY url ASC, time_start DESC
        """
    )

    body = "<h1>Endpoint status</h1>"
    body += "<table><thead>"
    for field in ["Endpoint", "Reached", "Status", "Time (UTC)", "Delay"]:
        body += f"<th>{field}</th>"
    body += "</thead>"
    for row in rows:
        if row["reached"]:
            body += "<tr>"
        else:
            body += "<tr class=unreachable>"
        body += (
            '<td><a href="'
            + urllib.parse.quote_plus(row["url"])
            + '">'
            + row["url"]
            + "</a></td>"
        )
        body += f"<td class=reached>{row['reached']}</td>"
        if row["reached"]:
            if 200 <= row["status"] < 300:
                body += f"<td class=ok>{row['status']}</td>"
            elif 400 <= row["status"] < 600:
                body += f"<td class=error>{row['status']}</td>"
            else:
                body += f"<td>{row['status']}</td>"
        else:
            body += f"<td class=error>{row['error']}</td>"
        body += f"<td>{row['time_start']}</td>"
        body += f"<td>{row['delay'].seconds:.2f}</td>"
        body += "</tr>"
    body += "</table>"

    return web.Response(text=make_html(body), content_type="text/html")


@routes.get("/{url}")
async def single(request: web.Request) -> web.Response:
    url = request.match_info.get("url")
    limit = max(1, int(request.query.get("limit", 10)))

    conn = request.config_dict["DB"]
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

    body = '<a href="/">Back to the front page</a>'
    body += f"<h1>History for {url}</h1>"
    body += "<table><thead>"
    for field in ["Reached", "Status", "Time (UTC)", "Delay"]:
        body += f"<th>{field}</th>"
    body += "</thead>"
    for row in rows:
        if row["reached"]:
            body += "<tr>"
        else:
            body += "<tr class=unreachable>"
        body += f"<td class=reached>{row['reached']}</td>"
        if row["reached"]:
            if 200 <= row["status"] < 300:
                body += f"<td class=ok>{row['status']}</td>"
            elif 400 <= row["status"] < 600:
                body += f"<td class=error>{row['status']}</td>"
            else:
                body += f"<td>{row['status']}</td>"
        else:
            body += f"<td class=error>{row['error']}</td>"
        body += f"<td>{row['time_start']}</td>"
        body += f"<td>{row['delay'].seconds:.2f}</td>"
        body += "</tr>"
    body += "</table>"

    if len(rows) == limit:
        body += f"<p>Showing first {limit} entries. "
        body += '<a href="?limit=' + str(limit + 10) + '">Show more</a>'
        body += "</p>"

    return web.Response(text=make_html(body), content_type="text/html")


def init_app() -> web.Application:
    cfg = config.load_or_die()
    app = web.Application()
    app.add_routes(routes)
    app.cleanup_ctx.append(init_db)
    return app


async def init_db(app: web.Application) -> AsyncIterator[None]:
    db = await postgres.connect()
    app["DB"] = db
    yield
    await db.close()


async def main():
    runner = web.AppRunner(init_app())
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8080)
    await site.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
