# Android Control Client

MVP Android support is the HTML5/PWA Control Client in a mobile browser.
Enter the 6-digit, 24-hour, 10-use pairing code from `omnidoer pair`, pair once,
then install the page to the home screen. The PWA keeps its local device key and
long-lived cached session, so normal credential, challenge, approval, and
takeover requests appear without re-pairing unless browser data is cleared or
the session is revoked.

Future native Android client plan:

- Secure password and TOTP input fields.
- Biometric unlock.
- Android Keystore-backed local keys.
- Screenshot blocking for sensitive screens.
- Push notifications for pending requests.
- E2EE pairing with Broker.
- Unified approval, credential, challenge, and takeover UI.
- Android passkey and biometric prompt integration.
- Low-latency WebRTC or CDP streaming for Human Takeover.
