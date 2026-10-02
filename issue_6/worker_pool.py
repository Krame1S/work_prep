import asyncio
from typing import Awaitable
from typing import Callable
from functools import wraps


class TemporaryError(Exception):
    ...

class RecievingBlockedError(Exception):
    ...

class EventItem:
    def __init__(self, event_id: int):
        self.event_id = event_id


class EventService:

    def __init__(self, handler: Callable[..., Awaitable[None]], queue_size, worker_count, max_attempts) -> None:
        self.handler = handler
        self.queue_size = queue_size
        self.worker_count = worker_count
        self.max_attempts = max_attempts
        self.failures: list[dict] = []
        self.successes: set = set()
        self._stopping: bool = False

        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self.workers: list[asyncio.Task] = []

    async def _worker(self):
        while True:
            event: EventItem = await self.queue.get()
            try:
                event_id = event.event_id
                if event_id in self.successes:
                    continue
                for attempt in range(1, self.max_attempts + 1):
                    try:
                        await self.handler(event)
                        self.successes.add(event_id)
                        break
                    except TemporaryError as e:
                        if attempt == self.max_attempts:
                            self.failures.append({'event_id': event_id, 'attempts': attempt, 'error': str(e)})  

                    except Exception as e:
                        self.failures.append({'event_id': event_id, 'attempts': attempt, 'error': str(e)})  
                        break
            finally:
                self.queue.task_done()


    async def start(self) -> None:
        for _ in range(self.worker_count):
            self.workers.append(asyncio.create_task(self._worker()))


    async def submit(self, event: EventItem) -> None:
        if self._stopping:
            raise RecievingBlockedError('Service is not accepting any requests at the moment')
        else:
            await self.queue.put(event)

    async def stop(self) -> None:
        self._stopping = True
        await self.queue.join()
        for t in self.workers:
            t.cancel()

        results = await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []
        for r in results:
            if isinstance(r, BaseException) and not isinstance(r, asyncio.CancelledError):
                raise r