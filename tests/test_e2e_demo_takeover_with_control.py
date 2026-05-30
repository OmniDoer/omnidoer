import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests.util_demo import DemoServerFixture
from omnidoer.omni_agent.demo_agent import run_task


class E2EDemoTakeoverTest(unittest.TestCase):
    def test_antibot_requires_takeover(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old = {key: os.environ.get(key) for key in ("OMNIDOER_HOME", "OMNIDOER_TAKEOVER_TEST_MODE", "OMNIDOER_TEST_TAKEOVER_ACTIONS")}
            os.environ["OMNIDOER_HOME"] = tmp
            os.environ["OMNIDOER_TAKEOVER_TEST_MODE"] = "1"
            os.environ["OMNIDOER_TEST_TAKEOVER_ACTIONS"] = "tap:100,100;type:user-completed;release"
            try:
                args = SimpleNamespace(task="处理 demo 网站的高强度反机器人页面", vault="", passphrase_env=None, demo_origin=demo.origin, control_origin="")
                self.assertEqual(run_task(args), 0)
                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertNotIn("user-completed", raw_audit)
                self.assertIn("takeover_released", raw_audit)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
