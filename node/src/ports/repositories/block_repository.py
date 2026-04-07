from abc import ABC, abstractmethod
from src.domain import Block


class IBlockRepository(ABC):
    _blocks: list[Block]

    @abstractmethod
    def add(self, block: Block) -> None:
        pass

    @abstractmethod
    def list(self) -> list[Block]:
        pass

    @abstractmethod
    def get_last_block(self) -> Block | None:
        pass
