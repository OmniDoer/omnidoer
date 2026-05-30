import os
import tempfile
import unittest
from types import SimpleNamespace

from tests.util_demo import DemoServerFixture
from omnidoer.omni_agent.demo_agent import run_task


class E2EDemoChallengeTest(unittest.TestCase):
    def test_captcha_requires_user_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, DemoServerFixture() as demo:
            old = {key: os.environ.get(key) for key in ("OMNIDOER_HOME", "OMNIDOER_CHALLENGE_TEST_MODE", "OMNIDOER_TEST_CAPTCHA_ACK")}
            os.environ["OMNIDOER_HOME"] = tmp
            os.environ["OMNIDOER_CHALLENGE_TEST_MODE"] = "1"
            os.environ["OMNIDOER_TEST_CAPTCHA_ACK"] = "user-completed"
            try:
                args = SimpleNamespace(task="处理 demo 网站的人机验证", vault="", passphrase_env=None, demo_origin=demo.origin, control_origin="")
                self.assertEqual(run_task(args), 0)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
