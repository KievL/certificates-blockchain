from src.ports.repositories import ITransactionRepository
from src.domain import Transaction


class TransactionInMemoryRepository(ITransactionRepository):
    def __init__(self):
        self._mempool: list[Transaction] = []

    def add(self, transaction: Transaction) -> None:
        if transaction in self._mempool:
            raise ValueError("Transaction already exists in mempool")

        self._mempool.append(transaction)

    def get(self, id: str) -> Transaction:
        for tx in self._mempool:
            if str(tx.id) == id:
                return tx
        raise ValueError("Transaction not found")

    def list(self) -> list[Transaction]:
        return self._mempool

    def remove(self, id: str) -> None:
        for tx in self._mempool:
            if tx.id == id:
                self._mempool.remove(tx)
                return
        raise ValueError("Transaction not found")

    def get_size(self) -> int:
        return len(self._mempool)

    def clear(self) -> None:
        self._mempool.clear()
