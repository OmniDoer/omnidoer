import os
import subprocess
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()

