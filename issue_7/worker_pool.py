import asyncio
from typing import Awaitable
from typing import Callable


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

        self._locks: dict[int, asyncio.Lock] = {}

        self._pending_submits: int = 0
        self._submits_done = asyncio.Event()
        self._submits_done.set()

        self._worker_error: BaseException | None = None
        self._failed = asyncio.Event()


    async def _wait_or_fail(self, aw):
        task = asyncio.ensure_future(aw)
        failed = asyncio.ensure_future(self._failed.wait())
        try:
            await asyncio.wait({task, failed}, return_when=asyncio.FIRST_COMPLETED)
            if task.done():
                return task.result()
            if self._worker_error is not None:
                raise self._worker_error
            raise RuntimeError('worker failure signalled without an error')
        finally:
            task.cancel()
            failed.cancel()


    async def _worker(self):
        while True:
            event: EventItem = await self.queue.get()
            try:
                event_id = event.event_id
                lock = self._locks.setdefault(event_id, asyncio.Lock())
                async with lock:
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
            except Exception as e:
                self._worker_error = e
                self._failed.set()
                raise
            finally:
                self.queue.task_done()


    async def start(self) -> None:
        for _ in range(self.worker_count):
            self.workers.append(asyncio.create_task(self._worker()))


    async def submit(self, event: EventItem) -> None:
        if self._worker_error is not None:
            raise self._worker_error
        if self._stopping:
            raise RecievingBlockedError('Service is not accepting any requests at the moment')
        else:
            self._pending_submits += 1
            self._submits_done.clear()
            try:
                await self._wait_or_fail(self.queue.put(event))
            finally:
                self._pending_submits -= 1
                if self._pending_submits == 0:
                    self._submits_done.set()


    async def stop(self) -> None:
        self._stopping = True
        try:
            await self._wait_or_fail(self._submits_done.wait())
            await self._wait_or_fail(self.queue.join())
        finally:
            for t in self.workers:
                t.cancel()

            results = await asyncio.gather(*self.workers, return_exceptions=True)
            self.workers = []

        for r in results:
            if isinstance(r, BaseException) and not isinstance(r, asyncio.CancelledError):
                raise r