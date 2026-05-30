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

## Local Demo

The mock checkout page is the only payment target for early MVP tests. Real
payments are out of scope until policy, audit, and redaction tests pass.
