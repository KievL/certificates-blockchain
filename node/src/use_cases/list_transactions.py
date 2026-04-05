from src.domain import Transaction
from src.ports.repositories import ITransactionRepository


class ListTransactions:
    def __init__(self, repository: ITransactionRepository):
        self.repository = repository

    def execute(self) -> list[Transaction]:
        return self.repository.list()
