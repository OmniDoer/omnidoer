import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omnidoer import paths


class PathsTest(unittest.TestCase):
    def test_default_home_is_user_home_not_current_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.pop("OMNIDOER_HOME", None)
            try:
                with patch("omnidoer.paths.Path.home", return_value=Path(tmp)):
                    self.assertEqual(paths.home(), (Path(tmp) / ".omnidoer").resolve())
            finally:
                if old_home is not None:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_env_home_still_overrides_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            try:
                os.environ["OMNIDOER_HOME"] = tmp
                self.assertEqual(paths.home(), Path(tmp).resolve())
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
