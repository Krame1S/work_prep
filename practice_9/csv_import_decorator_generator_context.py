import csv
import functools
import logging
import os
import tempfile
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class InvalidRowError(Exception):
    pass


class TooManyInvalidRowsError(Exception):
    pass


class ImportIOError(Exception):
    pass


def log_import(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info('Import started: %s', func.__name__)
        try:
            result = func(*args, **kwargs)
        except Exception:
            logger.exception('Import failed')
            raise
        logger.info(
            'Import finished: read=%d accepted=%d rejected=%d',
            result['read'], result['accepted'], result['rejected'],
        )
        return result
    return wrapper


def parse_row(row):
    sku = row['sku'].strip()
    if not sku:
        raise InvalidRowError('empty sku')

    raw_quantity = row['quantity']
    try:
        quantity = int(raw_quantity)
    except ValueError:
        raise InvalidRowError(
            f'quantity is not an integer: {raw_quantity!r}'
        ) from None
    if quantity < 0:
        raise InvalidRowError(f'quantity is negative: {quantity}')

    return {'sku': sku, 'quantity': quantity}


def iter_rows(file):
    reader = csv.DictReader(file)
    for number, row in enumerate(reader, start=1):
        yield number, row


@contextmanager
def atomic_output(destination):
    directory = os.path.dirname(os.path.abspath(destination))
    tmp = tempfile.NamedTemporaryFile(
        mode='w', encoding='utf-8', newline='',
        dir=directory, delete=False,
    )
    tmp_path = tmp.name
    try:
        yield tmp
        tmp.close()
        os.replace(tmp_path, destination)
    except BaseException:
        try:
            tmp.close()
        finally:
            try:
                os.remove(tmp_path)
            except FileNotFoundError:
                pass
        raise


@log_import
def import_inventory(source, destination, *, max_errors=2):
    """Импортирует остатки из CSV, сохраняя только корректные записи."""
    if max_errors < 0:
        raise ValueError('Maximum amount of errors cannot be negative')

    read = 0
    accepted = 0
    rejected = 0
    try:
        with open(source, 'r', encoding='utf-8', newline='') as src:
            with atomic_output(destination) as out:
                writer = csv.writer(out, lineterminator='\n')
                writer.writerow(['sku', 'quantity'])

                for number, row in iter_rows(src):
                    read += 1
                    try:
                        parsed = parse_row(row)
                    except InvalidRowError as exc:
                        rejected += 1
                        logger.warning('Row %d rejected: %s', number, exc)
                        if rejected > max_errors:
                            raise TooManyInvalidRowsError(
                                f'more than {max_errors} invalid rows '
                                f'(stopped at row {number})'
                            ) from exc
                        continue

                    writer.writerow([parsed['sku'], parsed['quantity']])
                    accepted += 1
    except OSError as exc:
        raise ImportIOError(f'file operation failed: {exc}') from exc

    return {'read': read, 'accepted': accepted, 'rejected': rejected}