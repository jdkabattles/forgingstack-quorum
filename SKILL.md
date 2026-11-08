# ForgingStack Quorum — skill for agents

Use this tool when an agent is about to act alone and the caller
wants N named approvers to sign off first, with a receipt to prove
it happened.

## When to use it

- Before a consequential action that should not be taken by one
  agent alone: deploying, spending, deleting, publishing, or
  changing shared state.
- When the approvers are named people (email addresses) and the
  number of approvals needed is explicit.

## When NOT to use it

- To decide if an action is wise, legal, or safe. This tool only
  collects approvals; the approvers decide the rest.
- When there are no approvers. Do not invent approvers to pass
  the check — a proposal needs at least one real approver, and at
  least as many approvers as the quorum requires.

## How to call it (MCP)

Tool: `create_proposal`
Arguments: `action`, `approvers` (email addresses),
`required_approvals`, `expires_at` (ISO 8601, in the future);
optional: `mandate_ref`.

Tool: `get_proposal`
Arguments: `proposal_id`.

## How to read the result

- `status: "pending"` → waiting on approvals. `approved_count`
  tells you how many of `required_approvals` are in.
- `status: "approved"` → quorum reached. Keep the `receipt_id`.
- `status: "expired"` → the proposal expired before quorum. No
  receipt; propose again if it is still wanted.
- `status: "rejected"` → the proposer rejected it.
- A proposal costs 1 credit. Approvals are free. An approval link
  works once; a used link cannot approve again.

## Status

Live, v0.1.2. API: https://forgingstack-quorum.jkbattles.workers.dev
Signup: POST /v1/signup with an email returns an API key once and
100 starter credits; email verification is required before the key
can create proposals. $10 for 1,000 credits via the billing
checkout; credits land after payment is verified.
