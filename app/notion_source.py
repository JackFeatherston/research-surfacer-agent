"""Live draft input via Notion's official hosted MCP server.

This connects to mcp.notion.com over the MCP Streamable HTTP transport, lists the
available tools, and calls Notion's fetch tool to pull a page's text. The first
run opens a browser for a one-time OAuth sign-in (any free Notion account works);
the token is cached to disk for later runs.

The Streamlit UI defaults to paste-text mode, so the demo runs without this path.
"""

import asyncio
import json
import webbrowser
from pathlib import Path

from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

from app.config import NOTION_MCP_URL, ROOT

TOKEN_FILE = ROOT / ".notion_token.json"


class _FileTokenStorage(TokenStorage):
    """Persist OAuth tokens and client registration in a local JSON file."""

    def _read(self) -> dict:
        return json.loads(TOKEN_FILE.read_text()) if TOKEN_FILE.exists() else {}

    def _write(self, patch: dict) -> None:
        TOKEN_FILE.write_text(json.dumps({**self._read(), **patch}, indent=2))

    async def get_tokens(self) -> OAuthToken | None:
        tokens = self._read().get("tokens")
        return OAuthToken.model_validate(tokens) if tokens else None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._write({"tokens": tokens.model_dump()})

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        info = self._read().get("client_info")
        return OAuthClientInformationFull.model_validate(info) if info else None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._write({"client_info": client_info.model_dump(mode="json")})


def _auth() -> OAuthClientProvider:
    return OAuthClientProvider(
        server_url=NOTION_MCP_URL,
        storage=_FileTokenStorage(),
        client_metadata=OAuthClientMetadata(
            client_name="Research Radar",
            redirect_uris=["http://localhost:8765/callback"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
        ),
        redirect_handler=lambda url: asyncio.to_thread(webbrowser.open, url),
        callback_handler=_await_callback,
    )


async def _await_callback() -> tuple[str, str | None]:
    """Run a one-shot local server to receive the OAuth redirect."""
    from aiohttp import web

    received: dict[str, str] = {}
    done = asyncio.Event()

    async def handle(request: web.Request) -> web.Response:
        received.update(request.query)
        done.set()
        return web.Response(text="Research Radar connected to Notion. You can close this tab.")

    app = web.Application()
    app.router.add_get("/callback", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8765)
    await site.start()
    await done.wait()
    await runner.cleanup()
    return received["code"], received.get("state")

# fetch text from notion page
async def _fetch(page: str) -> str:
    async with streamablehttp_client(NOTION_MCP_URL, auth=_auth()) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("notion-fetch", {"id": page})
            if result.isError:
                raise RuntimeError("\n".join(b.text for b in result.content if b.type == "text"))
            return "\n".join(b.text for b in result.content if b.type == "text")


def fetch_page(page: str) -> str:
    """Fetch the text of a Notion page by URL or id."""
    return asyncio.run(_fetch(page))
