"""OmniDoer sidecar package."""

from __future__ import annotations

import sys

# Keep source-tree validation grep deterministic after CLI/test runs.
sys.dont_write_bytecode = True

__all__ = ["__version__"]

__version__ = "0.1.0"
from omnidoer.version import __version__

__all__ = ["__version__"]
