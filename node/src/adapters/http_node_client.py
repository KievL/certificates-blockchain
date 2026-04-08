import logging
import httpx
from src.domain import Block
from src.ports.node_client import INodeClient

logger = logging.getLogger(__name__)


class HttpNodeClient(INodeClient):
    """Fetches the blockchain from peer nodes via HTTP (using httpx)."""

    async def get_chain(self, node_url: str) -> list[Block]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{node_url}/blocks")
                response.raise_for_status()
                return [Block(**b) for b in response.json()]
        except Exception as e:
            logger.error(f"Failed to fetch chain from {node_url}: {e}")
            return []
