"""Generic HTTP client wrapper."""

from typing import Any, Optional
import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class HTTPClient:
    """Async HTTP client wrapper."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Initialize HTTP client."""
        self.base_url = base_url
        self.timeout = timeout
        self.headers = headers or {}
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self.headers,
            )
        return self._client

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make GET request."""
        client = await self._get_client()
        logger.info(f"GET {self.base_url}{path}")
        return await client.get(path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make POST request."""
        client = await self._get_client()
        logger.info(f"POST {self.base_url}{path}")
        return await client.post(path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make PUT request."""
        client = await self._get_client()
        logger.info(f"PUT {self.base_url}{path}")
        return await client.put(path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make DELETE request."""
        client = await self._get_client()
        logger.info(f"DELETE {self.base_url}{path}")
        return await client.delete(path, **kwargs)

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "HTTPClient":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        await self.close()
