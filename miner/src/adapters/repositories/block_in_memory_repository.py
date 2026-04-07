from src.domain import Block
from src.ports.repositories.block_repository import IBlockRepository


class BlockInMemoryRepository(IBlockRepository):
    def __init__(self):
        self._blocks: list[Block] = []

    def add(self, block: Block) -> None:
        if block in self._blocks:
            raise ValueError("Block already exists")
        self._blocks.append(block)

    def list(self) -> list[Block]:
        return self._blocks

    def get_last_block(self) -> Block | None:
        return self._blocks[-1] if self._blocks else None
