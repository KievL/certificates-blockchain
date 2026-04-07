from src.domain import MiningBlock
from src.ports.repositories import IMiningBlockRepository


class MiningBlockInMemoryRepository(IMiningBlockRepository):
    def __init__(self):
        self._mining_blocks: list[MiningBlock] = []

    def add(self, mining_block: MiningBlock) -> None:
        if mining_block in self._mining_blocks:
            raise ValueError("Block already exists")
        self._mining_blocks.append(mining_block)

    def list(self) -> list[MiningBlock]:
        return self._mining_blocks
