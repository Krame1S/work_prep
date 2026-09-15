from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")

def iter_batches(items: Iterable[T], size: int) -> Iterator[list[T]]:
    if size < 1:
        raise ValueError('Batch size must be at least 1')
    it = iter(items)

    def batcher() -> Iterator[list[T]]:
        while True:
            batch = []
            for _ in range(size):
                try:
                    batch.append(next(it))
                except StopIteration:
                    break
            if not batch:
                break
            yield batch
    return batcher()