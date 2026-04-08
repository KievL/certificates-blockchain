from src.domain import Block
from src.ports.repositories.block_repository import IBlockRepository
from typing import List


class BlockInMemoryRepository(IBlockRepository):
    def __init__(self):
        self._blocks: list[Block] = []

    def add(self, block: Block) -> None:
        if block in self._blocks:
            raise ValueError("Block already exists")
        self._blocks.append(block)

    def list(self) -> list[Block]:
        return list(self._blocks)

    def get_last_block(self) -> Block | None:
        return self._blocks[-1] if self._blocks else None

    def get_chain(self) -> List[Block]:
        return list(self._blocks)

    def replace_chain(self, new_chain: List[Block]) -> None:
        self._blocks = list(new_chain)

    def get_block_by_hash(self, hash: str) -> Block | None:
        for block in self._blocks:
            if block.hash == hash:
                return block
        return None
