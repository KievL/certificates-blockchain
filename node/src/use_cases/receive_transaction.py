from src.domain import Transaction
from src.ports.repositories import ITransactionRepository


class ReceiveTransaction:
    def __init__(self, repository: ITransactionRepository):
        self.repository = repository

    def execute(self, transaction: Transaction) -> None:
        try:
            self.repository.add(transaction)
        except ValueError:
            pass
