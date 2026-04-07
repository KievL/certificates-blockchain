import asyncio
import logging
from typing import Callable, Awaitable

from src.ports.jobs.base_job_manager import IBaseJobManager

logger = logging.getLogger(__name__)


class AsyncIOJobManager(IBaseJobManager):
    """Implements IBaseJobManager using asyncio tasks."""

    def __init__(self):
        self._pending_task: asyncio.Task | None = None

    def schedule_job(
        self, delay: float, callback: Callable[[], Awaitable[None]]
    ) -> None:
        self.cancel_job()
        self._pending_task = asyncio.create_task(self._run_after(delay, callback))
        logger.info(f"Job scheduled in {delay:.2f}s")

    def cancel_job(self) -> None:
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()
            self._pending_task = None
            logger.info("Pending job cancelled")

    def is_job_pending(self) -> bool:
        return self._pending_task is not None and not self._pending_task.done()

    async def _run_after(
        self, delay: float, callback: Callable[[], Awaitable[None]]
    ) -> None:
        try:
            await asyncio.sleep(delay)
            self._pending_task = None
            await callback()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in scheduled job: {e}", exc_info=True)
