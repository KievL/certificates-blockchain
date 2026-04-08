from src.domain import Transaction
from src.ports.repositories import ITransactionRepository


class ReceiveTransaction:
    def __init__(self, repository: ITransactionRepository, public_key: str):
        self.repository = repository
        self.public_key = public_key

    def execute(self, transaction: Transaction) -> None:
        try:
            self.repository.add(transaction)
        except ValueError:
            pass
