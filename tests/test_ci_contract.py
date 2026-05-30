import pathlib
import unittest


class OmniDoerCiContractTest(unittest.TestCase):
    def test_ci_runs_sidecar_checks_on_main(self) -> None:
        workflow = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows" / "omnidoer-ci.yml"
        text = workflow.read_text()
        self.assertIn("- main", text)
        self.assertIn("- omnidoer-mvp", text)
        self.assertIn('python3 -m pip install -e ".[dev]"', text)
        self.assertIn("python3 -m pytest -q", text)
        self.assertIn("python3 omnidoer/scripts/secret_scan.py", text)
        self.assertIn("node --check omnidoer/omni_control/static/app.js", text)
        self.assertIn("--exclude-dir=__pycache__", text)


if __name__ == "__main__":
    unittest.main()
