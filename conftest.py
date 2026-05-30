"""Pytest process hygiene for source-tree safety scans."""

from __future__ import annotations

import sys


# The project acceptance grep scans the source tree after pytest. Avoid writing
# pyc caches that can produce misleading binary matches for intentionally
# documented strings such as OPENAI_API_KEY.
sys.dont_write_bytecode = True
