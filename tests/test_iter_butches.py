from collect_lazy_batches import iter_batches
import pytest

def test_standard_usage():
    batches = iter_batches(range(5), 2)
    assert list(batches) == [[0, 1], [2, 3], [4]]

def test_shorter_than_size():
    batches = iter_batches(range(3), 5)
    assert list(batches) == [[0, 1, 2]]

def test_empty_iterator():
    batches = iter_batches(range(0), 2)
    assert list(batches) == []

def test_no_reading_on_creation():
    read_count = 0

    def counting_generator():
        nonlocal read_count
        for i in range(5):
            read_count += 1
            yield i

    with pytest.raises(ValueError):
        iter_batches(counting_generator(), size=0)

    assert read_count == 0

def test_first_batch_doesnt_read_next():
    read_count = 0

    def counting_generator():
        nonlocal read_count
        for i in range(5):
            read_count += 1
            yield i

    gen = iter_batches(counting_generator(), size=2)
    first_batch = next(gen)

    assert first_batch == [0, 1]
    assert read_count == 2


def test_one_time_generator_consumed_in_single_pass():
    gen = map(lambda x: x, [1, 2, 3])
    result = list(iter_batches(gen, 2))
    assert result == [[1, 2], [3]]      # если бы наш gen читали бы несколько раз внутри iter_barches то результат был бы неверным


def test_mutating_yielded_batch_does_not_affect_next_batch():
    result_gen = iter_batches(range(5), 2)

    first_batch = next(result_gen)
    first_batch.append(100)

    second_batch = next(result_gen)

    assert second_batch == [2, 3]