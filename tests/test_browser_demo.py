import unittest
from http.cookiejar import CookieJar
from threading import Thread
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

from omnidoer.demo.server import DEMO_EMAIL, DEMO_PASSWORD, DEMO_USER, DemoHandler, ThreadingHTTPServer


class DemoSiteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        self.port = self.server.server_address[1]
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def post(self, path: str, data: dict[str, str]):
        return self.opener.open(Request(self.base + path, data=urlencode(data).encode(), method="POST"), timeout=5)

    def test_login_totp_invoice_flow(self) -> None:
        self.assertEqual(self.post("/login", {"email": DEMO_USER, "password": DEMO_PASSWORD}).status, 200)
        self.assertEqual(self.post("/totp", {"otp": "123456"}).status, 200)
        invoice = self.opener.open(self.base + "/invoice/download", timeout=5).read().decode()
        self.assertIn("INV-LOCAL-0001", invoice)

    def test_challenge_and_takeover_pages(self) -> None:
        for path in ("/captcha", "/antibot", "/passkey-mock", "/sms", "/email-code"):
            self.assertEqual(self.opener.open(self.base + path, timeout=5).status, 200)
        self.assertEqual(self.post("/captcha", {"ack": "user-completed"}).status, 200)
        self.assertEqual(self.post("/antibot", {"takeover": "user-completed"}).status, 200)

    def test_registration_logs_user_in_without_exposing_secret(self) -> None:
        self.assertEqual(self.opener.open(self.base + "/register", timeout=5).status, 200)
        self.assertEqual(
            self.post(
                "/register",
                {
                    "email": "new-demo@example.test",
                    "password": "new-demo-password",
                    "email_code": DEMO_EMAIL,
                    "terms": "yes",
                },
            ).status,
            200,
        )
        invoice = self.opener.open(self.base + "/invoice/download", timeout=5).read().decode()
        self.assertIn("INV-LOCAL-0001", invoice)

    def test_malicious_aliases(self) -> None:
        for path in (
            "/malicious/prompt-injection",
            "/malicious/iframe",
            "/malicious/form-action-mismatch",
            "/malicious/password-reveal",
            "/malicious/fake-token",
            "/malicious/fake-card",
        ):
            self.assertEqual(self.opener.open(self.base + path, timeout=5).status, 200)


if __name__ == "__main__":
    unittest.main()
