"""
Logging configuration for the GitHub Issues Service.

The logging configuration:
* sets the application logging level to ``INFO``;
* formats log messages with timestamps, log levels, and logger names; and
* writes log output to standard output for easy viewing in local development
  and containerized environments.

Author: Thanzeel Hassan
"""

import logging
import sys


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
