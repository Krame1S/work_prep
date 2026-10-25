import logging

import pytest

import csv_import_decorator_generator_context as mod
from csv_import_decorator_generator_context import (
    ImportIOError,
    InvalidRowError,
    TooManyInvalidRowsError,
    import_inventory,
    log_import,
    parse_row,
)

SAMPLE = (
    'sku,quantity\n'
    'A-100,12\n'
    'B-200,0\n'
    'C-300,abc\n'
    'D-400,-5\n'
    ',8\n'
    'E-500,3\n'
)


@pytest.fixture
def paths(tmp_path):
    return tmp_path / 'src.csv', tmp_path / 'dest.csv'


def make_source(src, text=SAMPLE):
    src.write_text(text, encoding='utf-8')


def files_in(tmp_path):
    return sorted(p.name for p in tmp_path.iterdir())


def test_parse_row_ok():
    assert parse_row({'sku': '  A-1 ', 'quantity': '0'}) == {'sku': 'A-1', 'quantity': 0}


@pytest.mark.parametrize(
    'row',
    [
        {'sku': '   ', 'quantity': '1'},
        {'sku': 'A', 'quantity': 'abc'},
        {'sku': 'A', 'quantity': '-5'},
    ],
)
def test_parse_row_invalid(row):
    with pytest.raises(InvalidRowError):
        parse_row(row)


def test_successful_import(paths):
    src, dest = paths
    make_source(src, 'sku,quantity\n  A-100 ,12\nB-200,0\nC-300,5\n')

    report = import_inventory(src, dest)

    assert dest.read_text(encoding='utf-8') == 'sku,quantity\nA-100,12\nB-200,0\nC-300,5\n'
    assert report == {'read': 3, 'accepted': 3, 'rejected': 0}


def test_example_from_task(paths):
    src, dest = paths
    make_source(src)

    report = import_inventory(src, dest, max_errors=3)

    assert dest.read_text(encoding='utf-8') == 'sku,quantity\nA-100,12\nB-200,0\nE-500,3\n'
    assert report == {'read': 6, 'accepted': 3, 'rejected': 3}


def test_header_only(paths):
    src, dest = paths
    make_source(src, 'sku,quantity\n')

    report = import_inventory(src, dest)

    assert dest.read_text(encoding='utf-8') == 'sku,quantity\n'
    assert report == {'read': 0, 'accepted': 0, 'rejected': 0}


def test_errors_exactly_at_limit(paths):
    src, dest = paths
    make_source(src)
    report = import_inventory(src, dest, max_errors=3)
    assert report['rejected'] == 3


def test_errors_exceed_limit_by_one(paths):
    src, dest = paths
    make_source(src)
    with pytest.raises(TooManyInvalidRowsError):
        import_inventory(src, dest, max_errors=2)


def test_zero_limit_stops_on_first_bad_row(paths):
    src, dest = paths
    make_source(src)
    with pytest.raises(TooManyInvalidRowsError):
        import_inventory(src, dest, max_errors=0)


def test_zero_limit_ok_on_clean_file(paths):
    src, dest = paths
    make_source(src, 'sku,quantity\nA,1\n')
    assert import_inventory(src, dest, max_errors=0)['accepted'] == 1


def test_negative_limit_raises_before_opening_files(paths, tmp_path):
    src, dest = paths
    with pytest.raises(ValueError):
        import_inventory(src, dest, max_errors=-1)
    assert files_in(tmp_path) == []


def test_generator_not_requested_after_limit_exceeded(paths, monkeypatch):
    src, dest = paths
    make_source(src)
    original = mod.iter_rows
    pulled = []

    def counting(file):
        for item in original(file):
            pulled.append(item[0])
            yield item

    monkeypatch.setattr(mod, 'iter_rows', counting)

    with pytest.raises(TooManyInvalidRowsError):
        import_inventory(src, dest, max_errors=2)

    assert pulled == [1, 2, 3, 4, 5]


def test_failure_keeps_old_file_and_removes_temp(paths, tmp_path):
    src, dest = paths
    make_source(src)
    dest.write_text('old\n', encoding='utf-8')

    with pytest.raises(TooManyInvalidRowsError):
        import_inventory(src, dest, max_errors=2)

    assert dest.read_text(encoding='utf-8') == 'old\n'
    assert files_in(tmp_path) == ['dest.csv', 'src.csv']


def test_failure_without_old_file_creates_nothing(paths, tmp_path):
    src, dest = paths
    make_source(src)

    with pytest.raises(TooManyInvalidRowsError):
        import_inventory(src, dest, max_errors=2)

    assert not dest.exists()
    assert files_in(tmp_path) == ['src.csv']


def test_replace_failure(paths, tmp_path, monkeypatch, caplog):
    src, dest = paths
    make_source(src)
    dest.write_text('old\n', encoding='utf-8')

    def bad_replace(a, b):
        raise OSError('replace failed')

    monkeypatch.setattr(mod.os, 'replace', bad_replace)

    with caplog.at_level(logging.INFO):
        with pytest.raises(ImportIOError):
            import_inventory(src, dest, max_errors=3)

    assert dest.read_text(encoding='utf-8') == 'old\n'
    assert files_in(tmp_path) == ['dest.csv', 'src.csv']
    assert not any('Import finished' in r.getMessage() for r in caplog.records)


def test_replace_failure_without_old_file(paths, tmp_path, monkeypatch):
    src, dest = paths
    make_source(src)
    monkeypatch.setattr(mod.os, 'replace', lambda a, b: (_ for _ in ()).throw(OSError('x')))

    with pytest.raises(ImportIOError):
        import_inventory(src, dest, max_errors=3)

    assert not dest.exists()
    assert files_in(tmp_path) == ['src.csv']


def test_open_failure_becomes_import_io_error(paths):
    src, dest = paths
    with pytest.raises(ImportIOError) as info:
        import_inventory(src, dest)
    assert isinstance(info.value.__cause__, FileNotFoundError)


def test_replace_error_is_the_cause(paths, monkeypatch):
    src, dest = paths
    make_source(src)
    original = OSError('replace failed')

    def bad_replace(a, b):
        raise original

    monkeypatch.setattr(mod.os, 'replace', bad_replace)

    with pytest.raises(ImportIOError) as info:
        import_inventory(src, dest, max_errors=3)
    assert info.value.__cause__ is original


def test_write_error_becomes_import_io_error(paths, tmp_path, monkeypatch):
    src, dest = paths
    make_source(src)
    original = OSError('disk full')

    class BadWriter:
        def writerow(self, row):
            raise original

    monkeypatch.setattr(mod.csv, 'writer', lambda *a, **k: BadWriter())

    with pytest.raises(ImportIOError) as info:
        import_inventory(src, dest)

    assert info.value.__cause__ is original
    assert files_in(tmp_path) == ['src.csv']


def test_type_error_propagates_unchanged(paths, tmp_path, monkeypatch, caplog):
    src, dest = paths
    make_source(src)
    error = TypeError('bug')

    def broken_parse(row):
        raise error

    monkeypatch.setattr(mod, 'parse_row', broken_parse)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(TypeError) as info:
            import_inventory(src, dest, max_errors=100)

    assert info.value is error
    assert not any('rejected' in r.getMessage() for r in caplog.records)
    assert files_in(tmp_path) == ['src.csv']


def test_log_contains_bad_rows(paths, caplog):
    src, dest = paths
    make_source(src)

    with caplog.at_level(logging.INFO):
        import_inventory(src, dest, max_errors=3)

    text = '\n'.join(r.getMessage() for r in caplog.records)
    assert 'Import started' in text
    assert 'Row 3 rejected: quantity is not an integer' in text
    assert 'Row 4 rejected: quantity is negative' in text
    assert 'Row 5 rejected: empty sku' in text
    assert 'read=6 accepted=3 rejected=3' in text


def test_log_on_limit_exceeded_has_row_and_traceback(paths, caplog):
    src, dest = paths
    make_source(src)

    with caplog.at_level(logging.INFO):
        with pytest.raises(TooManyInvalidRowsError):
            import_inventory(src, dest, max_errors=2)

    messages = [r.getMessage() for r in caplog.records]
    assert any('Row 5 rejected: empty sku' in m for m in messages)
    assert any(r.exc_info for r in caplog.records)
    assert not any('Import finished' in m for m in messages)


def test_decorator_preserves_metadata():
    assert import_inventory.__name__ == 'import_inventory'
    assert import_inventory.__doc__
    assert hasattr(import_inventory, '__wrapped__')


def test_decorator_returns_result_unchanged():
    expected = {'read': 1, 'accepted': 1, 'rejected': 0}

    @log_import
    def func():
        return expected

    assert func() is expected


def test_decorator_reraises_same_exception_object():
    error = RuntimeError()

    @log_import
    def func():
        raise error

    with pytest.raises(RuntimeError) as info:
        func()
    assert info.value is error