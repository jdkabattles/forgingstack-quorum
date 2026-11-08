"""MCP wrapper client for ForgingStack Quorum, v0.1.0.

An agent-native service must be usable by agents, not just by humans
with curl. MCP is the standard interface agents already speak, so the
wrapper exposes the same live REST API as MCP tools, with no duplicated
decision logic: every tool call goes through the REST API, so metering
and receipts stay in one place. The service itself is private; this
file is only a client.

Protocol: JSON-RPC 2.0 over stdio, no new dependencies (stdlib only).
Supported methods: initialize, ping, tools/list, tools/call.
Notifications (no id, e.g. notifications/initialized) get no response.

Environment:
  FORGINGSTACK_API_BASE  default https://forgingstack-quorum.jkbattles.workers.dev
  FORGINGSTACK_API_KEY   required; sign up via POST /v1/signup (key shown once)

Run:  python -m app.mcp_server
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get(
    "FORGINGSTACK_API_BASE",
    "https://forgingstack-quorum.jkbattles.workers.dev",
)
API_KEY = os.environ.get("FORGINGSTACK_API_KEY", "")

TOOLS = [
    {
        "name": "create_proposal",
        "description": "Propose an action for quorum approval. Each approver "
        "gets a one-time emailed link; when the required number approve, "
        "the proposal is approved and a hash-chained receipt is issued. "
        "Costs 1 credit per proposal; approvals are free.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to approve, non-empty, at most 500 characters.",
                },
                "approvers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Email addresses of the approvers (at least as many as required_approvals).",
                },
                "required_approvals": {
                    "type": "integer",
                    "description": "How many approvals are needed for quorum (1 or more).",
                },
                "expires_at": {
                    "type": "string",
                    "description": "Proposal expiry, ISO 8601, must be in the future.",
                },
                "mandate_ref": {
                    "type": "string",
                    "description": "Optional reference to a mandate (at most 500 characters).",
                },
            },
            "required": ["action", "approvers", "required_approvals", "expires_at"],
        },
    },
    {
        "name": "get_proposal",
        "description": "Fetch a proposal by id, with its approval state and, once approved, its receipt id.",
        "inputSchema": {
            "type": "object",
            "properties": {"proposal_id": {"type": "string"}},
            "required": ["proposal_id"],
        },
    },
    {
        "name": "get_credits",
        "description": "Remaining credit balance for the configured API key.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_receipt",
        "description": "Fetch a past quorum receipt by id.",
        "inputSchema": {
            "type": "object",
            "properties": {"receipt_id": {"type": "integer"}},
            "required": ["receipt_id"],
        },
    },
]


def _http(method, path, body=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
    )
    req.add_header("X-API-Key", API_KEY)
    req.add_header("Content-Type", "application/json")
    # A User-Agent is required: the default Python urllib agent is
    # rejected (Cloudflare 1010) through some egress paths.
    req.add_header("User-Agent", "ForgingStack-Quorum/0.1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {"detail": "api error"}


def _text(payload, is_error=False):
    return {
        "content": [{"type": "text", "text": json.dumps(payload)}],
        "isError": is_error,
    }


def handle(msg):
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "forgingstack-quorum", "version": "0.1.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "create_proposal":
            body = {k: args[k] for k in
                    ("action", "approvers", "required_approvals", "expires_at")
                    if k in args}
            if "mandate_ref" in args:
                body["mandate_ref"] = args["mandate_ref"]
            status, data = _http("POST", "/v1/proposals", body)
            return _text(data, is_error=status >= 400)
        if name == "get_proposal":
            status, data = _http(
                "GET", f"/v1/proposals/{args['proposal_id']}"
            )
            return _text(data, is_error=status >= 400)
        if name == "get_credits":
            status, data = _http("GET", "/v1/credits")
            return _text(data, is_error=status >= 400)
        if name == "get_receipt":
            status, data = _http(
                "GET", f"/v1/receipts/{args['receipt_id']}"
            )
            return _text(data, is_error=status >= 400)
        raise ValueError(f"unknown tool: {name}")
    raise ValueError(f"unknown method: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Notifications carry no id and get no response.
        if "id" not in msg:
            continue
        try:
            result = handle(msg)
            out = {"jsonrpc": "2.0", "id": msg["id"], "result": result}
        except Exception as exc:  # noqa: BLE001 - MCP error surface
            out = {
                "jsonrpc": "2.0", "id": msg["id"],
                "error": {"code": -32603, "message": str(exc)},
            }
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
