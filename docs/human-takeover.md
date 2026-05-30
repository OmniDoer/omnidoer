# Human Takeover

Human Takeover Mode is required for high-intensity anti-bot pages, interactive
CAPTCHA, slider challenges, WebAuthn/passkey prompts, device confirmations, or
any situation where automated continuation is unsafe.

Registration pages use the same control channel through Registration Handoff.
If a site requires a new account, Codex/OmniDoer may open the registration URL,
then `registration.request_user_handoff` pauses the Agent and proxies the
browser to the Control Client. The user completes account creation, email/SMS
verification, CAPTCHA, passkey setup, terms acknowledgement, and any required
profile fields directly in the controlled browser. OmniDoer does not automate
fake or bulk registration, and registration secrets or challenge answers are
not exposed to the LLM.

MVP streaming uses screenshot polling. `BrowserController.takeover_frame()`
returns a PNG frame with viewport metadata marked `for_control_client_only` and
`not_for_llm`. `BrowserController.apply_user_input_event()` maps Control Client
tap, click, double-click, long-press, drag, scroll, text, and key events to
Playwright mouse/keyboard input.

Frames are for the Control Client only and are not sent to the LLM. User input
events are audited by type only; text content is not logged.
