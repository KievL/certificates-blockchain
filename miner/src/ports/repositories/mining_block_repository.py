from abc import ABC, abstractmethod
from src.domain import MiningBlock


class IMiningBlockRepository(ABC):
    _mining_blocks: list[MiningBlock]

    @abstractmethod
    def add(self, mining_block: MiningBlock) -> None:
        pass

    @abstractmethod
    def list(self) -> list[MiningBlock]:
        pass
