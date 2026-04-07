from abc import ABC, abstractmethod
from typing import Callable, Awaitable


class IBaseJobManager(ABC):
    @abstractmethod
    def schedule_job(
        self, delay: float, callback: Callable[[], Awaitable[None]]
    ) -> None:
        """Schedules a new job."""
        pass

    @abstractmethod
    def cancel_job(self) -> None:
        """Cancels any currently pending job."""
        pass

    @abstractmethod
    def is_job_pending(self) -> bool:
        """Returns True if a job is currently scheduled and waiting."""
        pass
