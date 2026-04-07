from abc import ABC, abstractmethod
from pydantic import BaseModel


class IBasePublisher(ABC):
    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def publish(self, data: BaseModel, topic: str) -> None: ...
