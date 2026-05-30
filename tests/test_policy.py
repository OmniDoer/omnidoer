import unittest

from omnidoer.omni_policy import Decision, evaluate_credential_fill, origin_from_url, requires_approval
from omnidoer.omni_policy.policy import evaluate_challenge


class PolicyTest(unittest.TestCase):
    def test_origin_from_url(self) -> None:
        self.assertEqual(origin_from_url("https://Example.com/login"), "https://example.com")
        self.assertEqual(origin_from_url("http://localhost:8765/login"), "http://localhost:8765")

    def test_allows_exact_loopback_demo_origin(self) -> None:
        decision = evaluate_credential_fill(
            current_url="http://localhost:8765/login",
            allowed_origins={"http://localhost:8765"},
            top_level_frame=True,
            form_action_url="http://localhost:8765/login",
        )
        self.assertEqual(decision.decision, Decision.ALLOW)

    def test_blocks_unlisted_origin(self) -> None:
        decision = evaluate_credential_fill(
            current_url="https://evil.example/login",
            allowed_origins={"https://example.com"},
            top_level_frame=True,
            form_action_url="https://evil.example/login",
        )
        self.assertEqual(decision.decision, Decision.BLOCK)

    def test_blocks_non_loopback_http(self) -> None:
        decision = evaluate_credential_fill(
            current_url="http://example.com/login",
            allowed_origins={"http://example.com"},
            top_level_frame=True,
            form_action_url="http://example.com/login",
        )
        self.assertEqual(decision.decision, Decision.BLOCK)

    def test_blocks_iframe(self) -> None:
        decision = evaluate_credential_fill(
            current_url="https://example.com/login",
            allowed_origins={"https://example.com"},
            top_level_frame=False,
            form_action_url="https://example.com/login",
        )
        self.assertEqual(decision.decision, Decision.BLOCK)

    def test_blocks_form_action_mismatch(self) -> None:
        decision = evaluate_credential_fill(
            current_url="https://example.com/login",
            allowed_origins={"https://example.com"},
            top_level_frame=True,
            form_action_url="https://evil.example/steal",
        )
        self.assertEqual(decision.decision, Decision.BLOCK)

    def test_sensitive_actions_require_approval(self) -> None:
        self.assertEqual(requires_approval("payment_submit").decision, Decision.REQUIRE_APPROVAL)
        self.assertEqual(requires_approval("oauth_grant").decision, Decision.REQUIRE_APPROVAL)
        self.assertEqual(requires_approval("download_invoice").decision, Decision.ALLOW)

    def test_challenges_require_user_or_takeover(self) -> None:
        self.assertEqual(evaluate_challenge("captcha").decision, Decision.REQUIRE_USER_INTERACTION)
        self.assertEqual(evaluate_challenge("payment_3ds").decision, Decision.REQUIRE_USER_INTERACTION)
        self.assertEqual(evaluate_challenge("high_intensity_antibot").decision, Decision.REQUIRE_TAKEOVER)


if __name__ == "__main__":
    unittest.main()
