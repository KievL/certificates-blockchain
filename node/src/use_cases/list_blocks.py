from src.domain import Block
from src.ports.repositories.block_repository import IBlockRepository


class ListBlocks:
    def __init__(self, repository: IBlockRepository):
        self.repository = repository

    def execute(self) -> list[Block]:
        return self.repository.list()
