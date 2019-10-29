import argparse
import collections
from detect_ow import detect_ow
import logging
import os
import pytest

Args = collections.namedtuple('Args', 'dir port syslog_server tcp debug')

def patch_isdir(monkeypatch, is_dir):
    monkeypatch.setattr(os.path, "isdir", lambda _: is_dir)

def mock_args_port(monkeypatch, port):
    patch_isdir(monkeypatch, True)

    args = Args(dir="", port=port, syslog_server = "", tcp=False, debug=False)
    return args, {"DEFAULT": {}}

def test_port_not_int(monkeypatch):
    with pytest.raises(TypeError):
        args, config = mock_args_port(monkeypatch, "iv")
        detect_ow._merge_args_and_config(args, config)

def test_port_zero(monkeypatch):
    with pytest.raises(ValueError):
        args, config = mock_args_port(monkeypatch, 0)
        detect_ow._merge_args_and_config(args, config)

def test_port_negative(monkeypatch):
    with pytest.raises(ValueError):
        args, config = mock_args_port(monkeypatch, -1)
        detect_ow._merge_args_and_config(args, config)

def test_port_too_high(monkeypatch):
    with pytest.raises(ValueError):
        args, config = mock_args_port(monkeypatch, 65536)
        detect_ow._merge_args_and_config(args, config)

def mock_args_dir(monkeypatch, is_dir, error=None):
    patch_isdir(monkeypatch, is_dir)

    DIR = "/tmp"
    args = Args(dir=DIR, port=514, syslog_server = "", tcp=False, debug=False)

    return args, {"DEFAULT": {}}

def test_dir_no_exist(monkeypatch):
    with pytest.raises(ValueError):
        args, config = mock_args_dir(monkeypatch, False)
        detect_ow._merge_args_and_config(args, config)

@pytest.fixture
def config():
    return {
            "DEFAULT": {
                "dir": "/tmp",
                "port": 514,
                "syslog_server": "127.0.0.1",
                "protocol": "udp",
            }
        }

def test_invalid_protocol(monkeypatch, config):
    patch_isdir(monkeypatch, True)
    config['DEFAULT']['protocol'] = 'bogus'

    args = Args(dir=None, port=None, syslog_server=None, tcp=False, debug=False)

    with pytest.raises(ValueError):
        options = detect_ow._merge_args_and_config(args, config)


def test_args_override_dir(monkeypatch, config):
    patch_isdir(monkeypatch, True)

    expected_dir = "/some/new/dir"
    args = Args(dir=expected_dir, port=None, syslog_server=None, tcp=False, debug=False)
    options = detect_ow._merge_args_and_config(args, config)

    assert options.dir == expected_dir
    assert options.port == config['DEFAULT']['port']
    assert options.syslog_server == config['DEFAULT']['syslog_server']
    assert options.protocol == config['DEFAULT']['protocol']

def test_args_override_port(monkeypatch, config):
    patch_isdir(monkeypatch, True)

    expected_port = 600
    args = Args(dir=None, port=expected_port, syslog_server=None, tcp=False, debug=False)
    options = detect_ow._merge_args_and_config(args, config)

    assert options.dir == config['DEFAULT']['dir']
    assert options.port == expected_port
    assert options.syslog_server == config['DEFAULT']['syslog_server']
    assert options.protocol == config['DEFAULT']['protocol']

def test_args_override_syslog_server(monkeypatch, config):
    patch_isdir(monkeypatch, True)

    expected_syslog_server = "otherserver.domain"
    args = Args(dir=None, port=None, syslog_server=expected_syslog_server, tcp=False, debug=False)
    options = detect_ow._merge_args_and_config(args, config)

    assert options.dir == config['DEFAULT']['dir']
    assert options.port == config['DEFAULT']['port']
    assert options.syslog_server == expected_syslog_server
    assert options.protocol == config['DEFAULT']['protocol']

def test_args_override_protocol(monkeypatch, config):
    patch_isdir(monkeypatch, True)

    expected_protocol = 'tcp'
    args = Args(dir=None, port=None, syslog_server=None, tcp=True, debug=False)
    options = detect_ow._merge_args_and_config(args, config)

    assert options.dir == config['DEFAULT']['dir']
    assert options.port == config['DEFAULT']['port']
    assert options.syslog_server == config['DEFAULT']['syslog_server']
    assert options.protocol == expected_protocol

def test_has_interesting_events_false():
    interesting_events = {"IN_ATTRIB", "IN_CREATE", "IN_MOVED_TO"}
    received_events = ["IN_DELETE", "IN_ISDIR"]

    assert not detect_ow.has_interesting_events(received_events, interesting_events)

def test_has_interesting_events_true():
    interesting_events = {"IN_ATTRIB", "IN_CREATE", "IN_MOVED_TO"}

    received_events = ["IN_CREATE", "IN_ISDIR"]
    assert detect_ow.has_interesting_events(received_events, interesting_events)

    received_events = ["IN_MOVED_TO"]
    assert detect_ow.has_interesting_events(received_events, interesting_events)

MockStat = collections.namedtuple('MockStat', 'st_mode')
def mock_stat(monkeypatch, mode):
    ms = MockStat(st_mode=mode)
    monkeypatch.setattr(os, "stat", lambda _: ms)

def test_is_world_writable_true(monkeypatch):
    path = "/tmp/random_dir_kljafl"
    filename = "test_file"

    mock_stat(monkeypatch, 0o006)
    assert detect_ow.is_world_writable(path, filename)

    mock_stat(monkeypatch, 0o777)
    assert detect_ow.is_world_writable(path, filename)

    mock_stat(monkeypatch, 0o002)
    assert detect_ow.is_world_writable(path, filename)

    mock_stat(monkeypatch, 0o666)
    assert detect_ow.is_world_writable(path, filename)

def test_is_world_writable_false(monkeypatch):
    path = "/tmp/random_dir_kljafl"
    filename = "test_file"

    mock_stat(monkeypatch, 0o004)
    assert not detect_ow.is_world_writable(path, filename)

    mock_stat(monkeypatch, 0o770)
    assert not detect_ow.is_world_writable(path, filename)

    mock_stat(monkeypatch, 0o641)
    assert not detect_ow.is_world_writable(path, filename)

    mock_stat(monkeypatch, 0o665)
    assert not detect_ow.is_world_writable(path, filename)
