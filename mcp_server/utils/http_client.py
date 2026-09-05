"""Small async HTTP helper with retries for optional live enrichment."""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx


def live_data_enabled() -> bool:
    return os.getenv("MINIPS_ENABLE_LIVE_DATA", "false").lower() in {"1", "true", "yes"}


async def get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 12,
    retries: int = 3,
) -> dict[str, Any] | list[Any] | None:
    """GET JSON with exponential backoff; return None after all failures."""
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError):
            if attempt == retries - 1:
                return None
            await asyncio.sleep(0.4 * (2**attempt))
    return None
