# Human Takeover

Human Takeover Mode is required for high-intensity anti-bot pages, interactive
CAPTCHA, slider challenges, WebAuthn/passkey prompts, device confirmations, or
any situation where automated continuation is unsafe.

MVP streaming uses a screenshot-polling placeholder and event relay contract.
Frames are for the Control Client only and are not sent to the LLM. User input
events are not logged with text content.
