from abc import ABC, abstractmethod
from src.domain import Block


class INodeClient(ABC):
    @abstractmethod
    async def get_chain(self, node_url: str) -> list[Block]:
        """Fetch the blockchain from another node via HTTP."""
        pass
