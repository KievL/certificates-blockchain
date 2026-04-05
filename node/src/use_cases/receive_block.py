from src.domain import Block
from src.ports.repositories.block_repository import IBlockRepository
from src.ports.repositories.transaction_repository import ITransactionRepository


class ReceiveBlock:
    def __init__(
        self,
        block_repository: IBlockRepository,
        transaction_repository: ITransactionRepository,
    ):
        self.block_repository = block_repository
        self.transaction_repository = transaction_repository

    def execute(self, block: Block) -> None:
        try:
            self.block_repository.add(block)
            for tx in block.transactions:
                try:
                    self.transaction_repository.remove(tx.id)
                except ValueError:
                    pass
        except ValueError:
            pass
