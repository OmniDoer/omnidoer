# Payment Approval

OmniDoer can prepare a payment form, but it must not click the final payment,
purchase, transfer, subscription, or authorization button until the user
approves the structured review.

## Required Review Fields

- Merchant or payee.
- Amount.
- Currency.
- Item or service summary.
- Payment method summary, never full card data.
- Current top-level origin.
- Final form action origin.
- Final button text.
- Subscription or recurring billing status.
- Refund, cancellation, or renewal terms when visible.
- Risk level and policy reasons.

## Approval Decisions

- `deny`: do not submit.
- `approve_once`: submit this exact prepared action only.
- `cancel`: abandon the prepared action.

Approval is scoped to the reviewed details. If amount, merchant, origin, form
action, button text, or payment method summary changes, the approval is invalid.
OmniDoer records a SHA-256 review fingerprint over the scoped details and
recomputes it immediately before the approved click is allowed.

`browser.click` is policy-gated for sensitive final actions. Buttons that look
like payment submission, purchase, transfer, subscription, OAuth authorization,
or account deletion do not click immediately. The tool creates an approval
request with merchant/payee, amount, currency, origin, form action, final
button text, and after-approval result when those details are visible. Only an
approved request with the same review fingerprint can release that exact click.
The approval is consumed before the sensitive click is released, so replaying
the same approval id cannot submit the payment, transfer, upload, OAuth grant,
or account change a second time.

## Local Demo

The mock checkout page is the only payment target for early MVP tests. Real
payments are out of scope until policy, audit, and redaction tests pass.
