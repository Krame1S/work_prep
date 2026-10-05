import asyncio

import pytest

from worker_pool import EventItem
from worker_pool import EventService
from worker_pool import RecievingBlockedError
from worker_pool import TemporaryError

pytestmark = pytest.mark.asyncio


async def spin(times: int = 10) -> None:
    for _ in range(times):
        await asyncio.sleep(0)


def make_service(handler, queue_size=10, worker_count=1, max_attempts=3) -> EventService:
    return EventService(handler, queue_size, worker_count, max_attempts)


async def test_third_submit_waits_when_queue_is_full():
    handled = []

    async def handler(event):
        handled.append(event.event_id)

    service = make_service(handler, queue_size=2, worker_count=1)
    await service.submit(EventItem(1))
    await service.submit(EventItem(2))

    third = asyncio.create_task(service.submit(EventItem(3)))
    await spin()
    assert not third.done()
    assert service.queue.full()

    await service.start()
    await asyncio.wait_for(third, timeout=1)
    await service.stop()

    assert handled == [1, 2, 3]


async def test_active_handlers_do_not_exceed_worker_count():
    gate = asyncio.Event()
    active = 0
    max_active = 0
    done = []

    async def handler(event):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await gate.wait()
        active -= 1
        done.append(event.event_id)

    service = make_service(handler, queue_size=5, worker_count=2)
    for i in range(5):
        await service.submit(EventItem(i))
    await service.start()
    await spin()

    assert active == 2

    gate.set()
    await service.stop()

    assert max_active == 2
    assert sorted(done) == [0, 1, 2, 3, 4]


async def test_temporary_error_gives_exact_number_of_attempts():
    calls = []

    async def handler(event):
        calls.append(event.event_id)
        raise TemporaryError('temp')

    service = make_service(handler, max_attempts=3)
    await service.start()
    await service.submit(EventItem(1))
    await service.stop()

    assert len(calls) <= 3
    assert service.failures == [{'event_id': 1, 'attempts': 3, 'error': 'temp'}]
    assert 1 not in service.successes


async def test_temporary_error_then_success_has_no_failure():
    calls = []

    async def handler(event):
        calls.append(event.event_id)
        if len(calls) < 3:
            raise TemporaryError('temp')

    service = make_service(handler, max_attempts=5)
    await service.start()
    await service.submit(EventItem(1))
    await service.stop()

    assert len(calls) == 3
    assert service.failures == []
    assert 1 in service.successes


async def test_final_error_is_not_retried():
    calls = []

    async def handler(event):
        calls.append(event.event_id)
        raise ValueError('boom')

    service = make_service(handler, max_attempts=1)
    await service.start()
    await service.submit(EventItem(1))
    await service.stop()

    assert len(calls) == 1
    assert service.failures == [{'event_id': 1, 'attempts': 1, 'error': 'boom'}]


async def test_sequential_duplicate_creates_one_effect():
    effects = []

    async def handler(event):
        effects.append(event.event_id)

    service = make_service(handler, worker_count=1)
    await service.start()
    await service.submit(EventItem(1))
    await service.submit(EventItem(1))
    await service.stop()

    assert effects == [1]


async def test_bad_event_does_not_stop_neighbor():
    effects = []

    async def handler(event):
        if event.event_id == 1:
            raise ValueError('bad event')
        effects.append(event.event_id)

    service = make_service(handler, worker_count=1)
    await service.start()
    await service.submit(EventItem(1))
    await service.submit(EventItem(2))
    await service.stop()

    assert effects == [2]
    assert service.failures == [{'event_id': 1, 'attempts': 1, 'error': 'bad event'}]
    assert 2 in service.successes



async def test_stop_finishes_accepted_work_and_leaves_no_tasks():
    effects = []

    async def handler(event):
        await asyncio.sleep(0)
        effects.append(event.event_id)

    service = make_service(handler, queue_size=10, worker_count=3)
    await service.start()
    workers = list(service.workers)
    assert len(workers) == 3

    for i in range(10):
        await service.submit(EventItem(i))
    await service.stop()

    assert sorted(effects) == list(range(10))
    assert service.queue.empty()
    assert service.workers == []
    assert all(t.done() for t in workers)


async def test_submit_after_stop_started_raises_clear_error():
    gate = asyncio.Event()
    started = asyncio.Event()
    done = []

    async def handler(event):
        started.set()
        await gate.wait()
        done.append(event.event_id)

    service = make_service(handler)
    await service.start()
    await service.submit(EventItem(1))
    await started.wait()

    stop_task = asyncio.create_task(service.stop())
    await spin()

    with pytest.raises(RecievingBlockedError):
        await service.submit(EventItem(2))

    gate.set()
    await stop_task

    assert done == [1]


async def test_concurrent_duplicate_runs_handler_once():
    gate = asyncio.Event()
    started = asyncio.Event()
    calls = []

    async def handler(event):
        calls.append(event.event_id)
        started.set()
        await gate.wait()

    service = make_service(handler, queue_size=5, worker_count=2)
    await service.start()
    await service.submit(EventItem(1))
    await started.wait()

    await service.submit(EventItem(1))
    await spin()
    assert calls == [1]
    gate.set()
    await service.stop()

    assert calls == [1]
    assert service.successes == {1}
    assert service.failures == []


async def test_stop_processes_event_of_waiting_submit():
    gate = asyncio.Event()
    started = asyncio.Event()
    processed = []

    async def handler(event):
        started.set()
        await gate.wait()
        processed.append(event.event_id)

    service = make_service(handler, queue_size=1, worker_count=1)
    await service.start()

    await service.submit(EventItem('A'))
    await started.wait()
    await service.submit(EventItem('B'))

    submit_c = asyncio.create_task(service.submit(EventItem('C')))
    await spin()
    assert not submit_c.done()

    stop_task = asyncio.create_task(service.stop())
    await spin()
    assert not stop_task.done()

    gate.set()
    await asyncio.wait_for(stop_task, timeout=1)
    await asyncio.wait_for(submit_c, timeout=1)

    assert processed == ['A', 'B', 'C']
    assert service.queue.empty()
    assert service.workers == []


class BrokenEvent:
    @property
    def event_id(self):
        raise RuntimeError('internal failure')


async def test_internal_worker_failure_does_not_hang_stop():
    async def handler(event):
        pass

    service = make_service(handler, queue_size=5, worker_count=1)
    await service.submit(BrokenEvent())
    await service.submit(EventItem(2))
    await service.start()
    workers = list(service.workers)

    with pytest.raises(Exception):
        await asyncio.wait_for(service.stop(), timeout=1)

    assert service.workers == []
    assert all(t.done() for t in workers)


async def test_submit_raises_original_worker_error_after_failure():
    async def handler(event):
        pass

    service = make_service(handler, queue_size=5, worker_count=1)
    await service.start()
    await service.submit(BrokenEvent())
    await spin()

    with pytest.raises(RuntimeError, match='internal failure'):
        await service.submit(EventItem(2))

    with pytest.raises(RuntimeError, match='internal failure'):
        await asyncio.wait_for(service.stop(), timeout=1)