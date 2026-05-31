import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omnidoer.omni_cli.upgrade import _installed_codex_shim
from omnidoer.omni_cli.upgrade import _pip_install_command
from omnidoer.omni_cli.upgrade import _refresh_codex_shim_if_installed

ROOT = Path(__file__).resolve().parents[1]


class CodexShimScriptTest(unittest.TestCase):
    def test_install_and_uninstall_codex_shim_with_custom_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "codex"
            env = os.environ.copy()
            env["OMNIDOER_CODEX_SHIM_PATH"] = str(target)

            installed = subprocess.run(
                [str(ROOT / "omnidoer/scripts/install-codex-shim.sh")],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(installed.returncode, 0, installed.stderr)
            self.assertTrue(target.exists())
            self.assertIn("rollback:", installed.stdout)

            removed = subprocess.run(
                [str(ROOT / "omnidoer/scripts/uninstall-codex-shim.sh")],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(removed.returncode, 0, removed.stderr)
            self.assertFalse(target.exists())
            self.assertIn("removed OmniDoer Codex shim", removed.stdout)

    def test_upgrade_detects_and_refreshes_existing_codex_shim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            install_dir = Path(tmp) / "install"
            target = Path(tmp) / "codex"
            source = install_dir / "omnidoer/scripts/codex-omnidoer-shim.sh"
            source.parent.mkdir(parents=True)
            source.write_text("#!/bin/sh\n# new shim\nOMNIDOER_REAL_CODEX=/usr/bin/codex\n", encoding="utf-8")
            target.write_text("#!/bin/sh\n# old shim\nOMNIDOER_REAL_CODEX=/usr/bin/codex\n", encoding="utf-8")
            self.assertTrue(_installed_codex_shim(target))
            with patch.dict(os.environ, {"OMNIDOER_CODEX_SHIM_PATH": str(target)}):
                _refresh_codex_shim_if_installed(install_dir)
            self.assertEqual(target.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))

    def test_upgrade_adds_break_system_packages_only_when_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            install_dir = Path(tmp)
            with patch("omnidoer.omni_cli.upgrade._externally_managed_python", return_value=True):
                self.assertIn("--break-system-packages", _pip_install_command(install_dir))
            with patch("omnidoer.omni_cli.upgrade._externally_managed_python", return_value=False):
                self.assertNotIn("--break-system-packages", _pip_install_command(install_dir))


if __name__ == "__main__":
    unittest.main()
