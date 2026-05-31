import json
import stat
import unittest
from pathlib import Path


class NpmPackageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.package_dir = self.root / "npm" / "omnidoer"

    def test_package_metadata_is_public_scoped_bootstrap(self) -> None:
        package = json.loads((self.package_dir / "package.json").read_text())
        self.assertEqual(package["name"], "@omnidoer/omnidoer")
        self.assertFalse(package.get("private", False))
        self.assertEqual(package["bin"]["omnidoer"], "bin/omnidoer.js")
        self.assertEqual(package["publishConfig"]["access"], "public")

    def test_bin_bootstraps_without_embedded_secrets(self) -> None:
        script = self.package_dir / "bin" / "omnidoer.js"
        text = script.read_text()
        self.assertTrue(text.startswith("#!/usr/bin/env node"))
        self.assertIn("https://github.com/OmniDoer/omnidoer.git", text)
        self.assertIn("python -m omnidoer.omni_cli.main", (self.package_dir / "README.md").read_text())
        self.assertNotIn("github_pat_", text)
        self.assertNotIn("npm_", text)


if __name__ == "__main__":
    unittest.main()
