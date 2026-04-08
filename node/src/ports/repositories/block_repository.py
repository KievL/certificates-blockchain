from abc import ABC, abstractmethod
from src.domain import Block

from typing import List


class IBlockRepository(ABC):
    _blocks: List[Block]

    @abstractmethod
    def add(self, block: Block) -> None:
        pass

    @abstractmethod
    def list(self) -> List[Block]:
        pass

    @abstractmethod
    def get_last_block(self) -> Block | None:
        pass

    @abstractmethod
    def get_chain(self) -> List[Block]:
        """Return the main chain (ordered list of blocks)."""
        pass

    @abstractmethod
    def replace_chain(self, new_chain: List[Block]) -> None:
        """Replace the entire chain (used in consensus and fork resolution)."""
        pass

    @abstractmethod
    def get_block_by_hash(self, hash: str) -> Block | None:
        """Find a block by its hash."""
        pass
