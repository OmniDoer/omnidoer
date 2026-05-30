import unittest

from omnidoer.omni_telegram.bridge import status


class TelegramTest(unittest.TestCase):
    def test_telegram_disabled_for_sensitive_channels(self) -> None:
        text = status()
        self.assertIn("disabled", text)
        self.assertIn("Control Client", text)


if __name__ == "__main__":
    unittest.main()
