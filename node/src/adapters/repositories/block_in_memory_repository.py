from src.domain import Block
from src.ports.repositories.block_repository import IBlockRepository


class BlockInMemoryRepository(IBlockRepository):
    def __init__(self):
        self.blocks: list[Block] = []

    def add(self, block: Block) -> None:
        if block in self.blocks:
            raise ValueError("Block already exists")
        self.blocks.append(block)

    def list(self) -> list[Block]:
        return self.blocks

    def get_last_block(self) -> Block | None:
        return self.blocks[-1] if self.blocks else None
