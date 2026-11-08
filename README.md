# ForgingStack Quorum

Before an agent acts alone, get the quorum. One proposal, N approvals, one receipt.

mcp-name: io.github.jdkabattles/forgingstack-quorum

This is the **public client** for Quorum. The service itself —
the approval flow, the receipt chain, the key store, and billing —
runs on ForgingStack's private service and is **not** in this repo.
Copying this repo does not give you the service: you still need an
API key and credits, from signup below.

Live API: https://forgingstack-quorum.jkbattles.workers.dev

## How it works

1. You propose an action, name the approvers, and set how many
   approvals are needed (N) and when the proposal expires.
2. Each approver gets a one-time emailed link. Approvals are free.
3. At quorum the proposal is approved and a hash-chained receipt is
   issued. If it expires first, it expires — no receipt, and the
   proposal cannot be approved afterwards.
4. You can also reject a pending proposal yourself.

What it does **not** do: decide if an action is wise, legal, or
safe. Quorum only — the approvers decide the rest.

## Signup

```bash
curl -X POST https://forgingstack-quorum.jkbattles.workers.dev/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com"}'
```

Returns an API key **once** and 100 starter credits. Save the key
immediately — it is stored only as a hash and cannot be shown again.
Click the verification link in the signup email before the key can
create proposals (if the mail does not arrive, check spam, or
`POST /v1/verify/resend`).

## Create a proposal

```bash
curl -X POST https://forgingstack-quorum.jkbattles.workers.dev/v1/proposals \
  -H "X-API-Key: YOUR_PRIMARY_KEY" -H "Content-Type: application/json" \
  -d '{"action":"deploy the new build","approvers":["a@example.com","b@example.com"],"required_approvals":2,"expires_at":"2027-01-01T00:00:00Z"}'
```

Returns the proposal (201) with its approval state and which
approval emails were sent. Read it back with
`GET /v1/proposals/{id}`, list yours with `GET /v1/proposals`,
reject a pending one with `POST /v1/proposals/{id}/reject`.
Approvers approve by clicking the link in their email — each link
works once. The receipt, once issued, is at `GET /v1/receipts/{id}`.

## Use it (MCP, stdio)

Set the key, then run the MCP server in this repo:

```bash
export FORGINGSTACK_API_KEY="your-key-here"
python -m app.mcp_server
```

Tools: `create_proposal`, `get_proposal`, `get_credits`, `get_receipt`.
See `SKILL.md` for when to use it and when not to.

## Price

1 credit per proposal. Approvals are free. 100 starter credits on
signup. $10 for 1,000 credits via `POST /v1/billing/checkout`
(Payment Link). Credits land after payment is verified — usually
within the hour.

## Files in this repo

- `app/mcp_server.py` — MCP wrapper client (stdio, stdlib only)
- `SKILL.md` — when to use it, how to read the result
- `agent-card.json` — A2A-style discovery card
- `server.json` — MCP Registry metadata
- `pyproject.toml` — package metadata for the MCP client
- `llms.txt` — short index for language-model readers
