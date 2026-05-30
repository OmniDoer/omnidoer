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

Each streamed frame includes `frame_id`, `captured_at`, viewport metadata, and
`input_binding_required`. The Control Client attaches the visible `frame_id` to
touch, keyboard, and text input. The Control Service records the last delivered
frame and rejects stale or mismatched input before it reaches the browser
worker, preventing a tap from an old phone frame from being replayed onto a
newly navigated page.
The Control Client also shows frame freshness and refuses to send user input
from a stale frame, refreshing the browser projection before the user tries
again.
For small mobile screens, the Control Client can zoom the visible browser frame
up to 300% and switch into view-pan mode. Zoom and pan affect only the
control-only projection; touch coordinates are still mapped back to the
original screenshot pixel space and sent with the visible `frame_id`.
If frame polling drops during a mobile network transition, the Control Client
keeps the last browser frame visible and marks the stream as reconnecting
instead of blanking the challenge. The same freshness guard still turns that
retained frame stale and blocks input until a new current frame arrives.

Frames are for the Control Client only and are not sent to the LLM. User input
events are allowlisted, length-limited, and audited by type only; text content,
challenge answers, passkey material, and registration secrets are not logged.
