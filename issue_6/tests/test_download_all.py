import pytest
from concurrent_url_downloader import download_all
import asyncio


class FakeError(Exception):
    pass


async def test_active_calls_always_less_then_limit():
    urls = ['1', '2', '3', '4', '5']

    def make_fetch():
        call_count = 0
        release = asyncio.Event()
        entered = asyncio.Event()

        async def fetch(url):
            nonlocal call_count
            call_count += 1
            assert call_count <= 2
            if call_count == 2:
                entered.set()
            await release.wait()
            call_count -= 1
            return url

        return fetch, entered, release

    fake_fetch, entered, release = make_fetch()
    task = asyncio.create_task(download_all(urls, limit=2, fetch=fake_fetch))
    await entered.wait()
    release.set()
    await task


async def test_reverse_completion_preserves_order():
    urls = ['1', '2', '3']

    def make_fetch():
        events = {u: asyncio.Event() for u in urls}
        started = {u: asyncio.Event() for u in urls}
        finished = {u: asyncio.Event() for u in urls}

        async def fetch(url):
            started[url].set()
            await events[url].wait()
            finished[url].set()
            return url

        return fetch, events, started, finished

    fake_fetch, events, started, finished = make_fetch()
    task = asyncio.create_task(download_all(urls, limit=3, fetch=fake_fetch))

    for u in urls:
        await started[u].wait()

    events['3'].set()
    await finished['3'].wait()

    events['2'].set()
    await finished['2'].wait()

    events['1'].set()
    await finished['1'].wait()

    result = await task
    assert result == ['1', '2', '3']


async def test_error_propagates():
    urls = ['1', '2', '3']

    def make_fetch():
        events = {u: asyncio.Event() for u in urls}

        async def fetch(url):
            if url == '2':
                raise FakeError()
            await events[url].wait()
            return url

        return fetch

    fake_fetch = make_fetch()
    task = asyncio.create_task(download_all(urls, limit=3, fetch=fake_fetch))

    with pytest.raises(FakeError):
        await task


async def test_neighbors_cancelled_and_cleaned_up_on_error():
    urls = ['1', '2', '3']
    cleaned_up = set()
    started = {'1': asyncio.Event(), '3': asyncio.Event()}
    hang = asyncio.Event()
    release_error = asyncio.Event()

    async def fake_fetch(url):
        if url == '2':
            await release_error.wait()
            raise FakeError()
        started[url].set()
        try:
            await hang.wait()
        except asyncio.CancelledError:
            cleaned_up.add(url)
            raise
        return url

    task = asyncio.create_task(download_all(urls, limit=3, fetch=fake_fetch))

    await started['1'].wait()
    await started['3'].wait()

    release_error.set()

    with pytest.raises(FakeError):
        await task

    assert cleaned_up == {'1', '3'}


async def test_external_cancellation_cleans_up_children():
    urls = ['1', '2', '3']
    cleaned_up = set()
    started = {u: asyncio.Event() for u in urls}
    hang = asyncio.Event()

    async def fake_fetch(url):
        started[url].set()
        try:
            await hang.wait()
        except asyncio.CancelledError:
            cleaned_up.add(url)
            raise
        return url

    task = asyncio.create_task(download_all(urls, limit=3, fetch=fake_fetch))

    for e in started.values():
        await e.wait()

    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert cleaned_up == {'1', '2', '3'}