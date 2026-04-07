from abc import ABC, abstractmethod


class IBaseConsumer(ABC):
    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def process_message(self, data: dict) -> None:
        pass
