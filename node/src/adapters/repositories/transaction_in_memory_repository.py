from src.ports.repositories import ITransactionRepository
from src.domain import Transaction


class TransactionInMemoryRepository(ITransactionRepository):
    def __init__(self):
        self.mempool: list[Transaction] = []

    def add(self, transaction: Transaction) -> None:
        if transaction in self.mempool:
            raise ValueError("Transaction already exists in mempool")

        self.mempool.append(transaction)

    def get(self, id: str) -> Transaction:
        for tx in self.mempool:
            if str(tx.id) == id:
                return tx
        raise ValueError("Transaction not found")

    def list(self) -> list[Transaction]:
        return self.mempool

    def remove(self, id: str) -> None:
        for tx in self.mempool:
            if str(tx.id) == id:
                self.mempool.remove(tx)
                return
        raise ValueError("Transaction not found")

    def get_size(self) -> int:
        return len(self.mempool)

    def clear(self) -> None:
        self.mempool.clear()
