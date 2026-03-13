# conftest.py
# Shared fixtures: logger, session, and API client

import logging
import os
from datetime import datetime, timezone

import pytest
import requests

from tests.api_client import PostsClient

BASE_URL = os.getenv("BASE_URL", "https://jsonplaceholder.typicode.com")
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "10"))
LOG_FILE = os.getenv("API_TEST_LOG_FILE", "api_test_run.log")
PREVIEW_COUNT = int(os.getenv("CONSOLE_JSON_LIST_PREVIEW_COUNT", "3"))


def _configure_logger():
    logger = logging.getLogger("api_tests")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if pytest reloads
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (INFO and above)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)

    # File handler (DEBUG and above)
    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(sh)
    logger.addHandler(fh)

    # Run header
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    logger.info("=" * 90)
    logger.info("TEST RUN START (UTC): %s", now)
    logger.info("Working dir: %s", os.getcwd())
    logger.info("Log file   : %s", os.path.abspath(LOG_FILE))
    logger.info("=" * 90)

    return logger


@pytest.fixture(scope="session")
def logger():
    return _configure_logger()


@pytest.fixture(scope="session")
def http_session():
    """
    Reuse a single Session across all tests:
    - faster
    - consistent connection pooling
    """
    s = requests.Session()
    yield s
    s.close()


@pytest.fixture(scope="session")
def posts_client(http_session, logger):
    return PostsClient(
        session=http_session,
        base_url=BASE_URL,
        timeout=TIMEOUT_SECONDS,
        logger=logger,
        preview_count=PREVIEW_COUNT,
    )


@pytest.fixture(autouse=True)
def log_test_start_end(request, logger):
    """Prints which test is running (very useful during interview/demo)."""
    logger.info("--- TEST START: %s ---", request.node.name)
    yield
    logger.info("--- TEST END  : %s ---", request.node.name)
