# app/integrations/base_ai_client.py
"""Base class for AI service clients."""

from typing import Optional

from app.integrations.http_client import HTTPClient


class BaseAIClient:
    """
    Base class for AI service clients with common HTTP configuration.
    
    Provides:
    - HTTPClient initialization with base URL and timeout
    - Optional API key authentication via Bearer token
    - Consistent client setup across all AI integrations
    
    Subclasses should apply @with_circuit_breaker and @with_retry decorators
    to their specific methods as needed.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize AI client with HTTP configuration.
        
        Args:
            base_url: Base URL for the AI service
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = HTTPClient(
            base_url=base_url,
            timeout=int(timeout),
            headers=headers,
        )

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self.client.close()
