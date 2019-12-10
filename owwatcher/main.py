#!/usr/bin/env python3

import argparse
import collections
import configparser
from .options import Options
import os
from .owwatcher_logger_configurer import OWWatcherLoggerConfigurer
from .owwatcher import OWWatcher
import signal
import sys

# Creating null loggers allows pytest test suite to run as logging is not
# necessarily configured for each unit test run.
_LOGGER = OWWatcherLoggerConfigurer.get_null_logger()
_SYSLOG_LOGGER = OWWatcherLoggerConfigurer.get_null_logger()

_OWWATCHER = None

def main():
    global _OWWATCHER
    try:
        is_snap = check_if_snap()
        (parser, args) = _parse_args(is_snap)
        config = _read_config(args.config_path)
        options = Options(args, config, is_snap)
        configure_logging(options.debug, options.syslog_server, options.syslog_port, options.log_file)
        _OWWATCHER = OWWatcher(_LOGGER, _SYSLOG_LOGGER, is_snap)
        register_signal_handlers()
    except Exception as ex:
        print("Error during initialization: %s" % str(ex), file=sys.stderr)
        sys.exit(1)

    _LOGGER.info("Starting owwatcher...")
    _log_config_options(options)

    _OWWATCHER.run(options.dirs)

def check_if_snap():
    return 'SNAP_DATA' in os.environ

def _parse_args(is_snap):
    default_config_file = Options.get_default_config_file(is_snap)

    parser = argparse.ArgumentParser(
            description="Watch a directory for newly created world writable "\
                    "files and directories. Log events to a syslog server.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config-path', action='store', default=default_config_file,
                        help='A config file to read settings from. Command line ' \
                              'arguments override values read from the config file. ' \
                              'If the config file does not exist, owwatcher will ' \
                              'log a warning and ignore the specified config file')
    parser.add_argument('-d', '--dirs', action='store',
                        help='A comma-separated list of directories to watch ' \
                             'for world writable files/dirs')
    parser.add_argument('-p', '--syslog-port', action='store', type=int,
                        help='The port that the syslog server is listening on')
    parser.add_argument('-s', '--syslog-server', action='store',
                        help='IP address or hostname of a syslog server')
    parser.add_argument('-t', '--tcp', action='store_true',
                        help='Use TCP instead of UDP to send syslog messages.')
    parser.add_argument('-l', '--log-file', action='store',
                        help='Path to log file')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')

    args = parser.parse_args()

    return parser, args

def _read_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)

    return config

def configure_logging(debug, syslog_server, syslog_port, log_file):
    global _LOGGER
    global _SYSLOG_LOGGER

    logger_configurer = OWWatcherLoggerConfigurer(debug, syslog_server, syslog_port, log_file)
    _LOGGER = logger_configurer.get_owwatcher_logger()
    _SYSLOG_LOGGER = logger_configurer.get_syslog_logger()

def register_signal_handlers():
    signal.signal(signal.SIGINT, receive_signal)
    signal.signal(signal.SIGTERM, receive_signal)

def receive_signal(signum, stack_frame):
    _LOGGER.debug("Received signal %s" % signal.Signals(signum))
    _LOGGER.info("Cleaning up and exiting")

    if _OWWATCHER is not None:
        _OWWATCHER.stop()

def _log_config_options(options):
    _LOGGER.info('Option "dirs": %s', ','.join(options.dirs))
    _LOGGER.info('Option "syslog_server": %s', options.syslog_server)
    _LOGGER.info('Option "syslog_port": %s', options.syslog_port)
    _LOGGER.info('Option "protocol": %s', options.protocol)
    _LOGGER.info('Option "log_file": %s', options.log_file)
    _LOGGER.info('Option "debug": %s', options.debug)

if __name__ == "__main__":
    main()