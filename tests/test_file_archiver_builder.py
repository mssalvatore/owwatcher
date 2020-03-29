import logging
import pytest
from owwatcher import file_archiver_builder

@pytest.fixture
def null_logger():
    null_logger = logging.getLogger('owwatcher.null')
    null_logger.addHandler(logging.NullHandler())

    return null_logger

def test_archive_path(null_logger):
    archive_path = "/tmp/archive"
    fab = file_archiver_builder.FileArchiverBuilder(null_logger, archive_path)
    fa = fab.build_file_archiver(None)

    assert fa.archive_path == archive_path

def test_watch_dir():
    archive_path = "/tmp/archive"
    watch_dir = "/tmp/watch_dir"
    fab = file_archiver_builder.FileArchiverBuilder(null_logger, archive_path)
    fa = fab.build_file_archiver(watch_dir)

    assert fa.watch_dir == watch_dir

def test_queue_not_none():
    archive_path = "/tmp/archive"
    watch_dir = "/tmp/watch_dir"
    fab = file_archiver_builder.FileArchiverBuilder(null_logger, archive_path)
    fa = fab.build_file_archiver(watch_dir)

    assert fa.archive_queue is not None