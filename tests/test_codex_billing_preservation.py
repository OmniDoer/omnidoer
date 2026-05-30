import pathlib
import unittest


class CodexBillingPreservationTest(unittest.TestCase):
    def test_no_default_openai_api_client_path(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        scanned = []
        for base in (root / "omnidoer", root / "tests"):
            for path in base.rglob("*.py"):
                text = path.read_text()
                scanned.append(path)
                self.assertNotIn("from " + "openai import", text, path)
                self.assertNotIn("Open" + "AI(", text, path)
        self.assertTrue(scanned)

    def test_codex_auth_billing_files_are_not_modified_by_sidecar(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1]
        for path in (root / "omnidoer").rglob("*.py"):
            text = path.read_text()
            if "auth.json" in text:
                self.assertEqual(path.name, "doctor.py")
                self.assertNotIn("read_text", text)
                self.assertNotIn("write_text", text)


if __name__ == "__main__":
    unittest.main()
