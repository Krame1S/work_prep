from collections.abc import Awaitable, Callable, Sequence
import asyncio


async def download_all(
    urls: Sequence[str],
    *,
    limit: int,
    fetch: Callable[[str], Awaitable[bytes]],
) -> list[bytes]:
    if limit < 1:
        raise ValueError()
    if not urls:
        return []

    sema = asyncio.Semaphore(limit)

    async def instance(url: str) -> bytes:
        async with sema:
            return await fetch(url)

    tasks = []
    for url in urls:
        tasks.append(asyncio.create_task(instance(url)))

    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        for t in tasks:
            if t.done() and not t.cancelled() and t.exception() is not None:
                raise t.exception()

        return [t.result() for t in tasks]

    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)