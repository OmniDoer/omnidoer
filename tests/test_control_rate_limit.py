import unittest

from omnidoer.omni_control.rate_limit import RateLimiter


class ControlRateLimitTest(unittest.TestCase):
    def test_lockout_after_failures(self) -> None:
        limiter = RateLimiter(max_attempts=2, window_seconds=60, lockout_seconds=120)
        limiter.record_failure("pair:1", now=100)
        limiter.record_failure("pair:1", now=101)
        with self.assertRaises(PermissionError):
            limiter.check("pair:1", now=102)
        with self.assertRaises(PermissionError):
            limiter.check("pair:1", now=150)
        limiter.check("pair:1", now=223)


if __name__ == "__main__":
    unittest.main()
