"""msteams: read Microsoft Teams channels, messages and chats (Microsoft Graph), and post messages. Posting needs --write."""
import argparse
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)

GRAPH = c.setting("TEAMS_GRAPH_URL", "https://graph.microsoft.com/v1.0")
LOGIN = c.setting("TEAMS_LOGIN_URL", "https://login.microsoftonline.com")
SCOPES = ("offline_access User.Read Team.ReadBasic.All Channel.ReadBasic.All ChannelMessage.Read.All "
          "ChannelMessage.Send Chat.Read ChatMessage.Send")
TOKEN_FILE = HERE / ".token.json"   # secret: never print it
FORM = {"Content-Type": "application/x-www-form-urlencoded"}


# ---------- sign-in (device code: the user signs in once in a browser) ----------

def _oauth(path, data):
    tenant, client = c.need("TEAMS_TENANT_ID", "TEAMS_CLIENT_ID")
    return c.http("POST", f"{LOGIN}/{tenant}/oauth2/v2.0/{path}", FORM, urllib.parse.urlencode({"client_id": client, **data}))


def _save_token(tok, old_refresh=None):
    TOKEN_FILE.write_text(json.dumps({
        "access_token": tok["access_token"],
        "refresh_token": tok.get("refresh_token") or old_refresh,
        "expires_at": time.time() + int(tok.get("expires_in", 3600)) - 120,
    }), encoding="utf-8")
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass


def access_token():
    if c.setting("TEAMS_ACCESS_TOKEN"):
        return c.setting("TEAMS_ACCESS_TOKEN")
    if not TOKEN_FILE.exists():
        raise c.ConnectorError("Not signed in to Microsoft Teams.",
                               "Run: python connectors/msteams/run.py login, then the user signs in in the browser.")
    tok = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    if tok.get("expires_at", 0) > time.time():
        return tok["access_token"]
    if not tok.get("refresh_token"):
        raise c.ConnectorError("The Teams sign-in expired.", "Run: python connectors/msteams/run.py login")
    try:
        new = _oauth("token", {"grant_type": "refresh_token", "refresh_token": tok["refresh_token"], "scope": SCOPES})
    except c.ConnectorError:
        raise c.ConnectorError("The Teams sign-in expired.", "Run: python connectors/msteams/run.py login") from None
    _save_token(new, tok["refresh_token"])
    return new["access_token"]


def graph(method, path, params=None, body=None):
    url = path if path.startswith("http") else GRAPH + path
    if params:
        url += "?" + "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    return c.http(method, url, {"Authorization": f"Bearer {access_token()}"}, body)


def graph_list(path, limit, params=None):
    """Follow @odata.nextLink pages until `limit` items."""
    items, res = [], graph("GET", path, {**(params or {}), "$top": min(limit, 50)})
    while True:
        items += res.get("value", [])
        if len(items) >= limit or not res.get("@odata.nextLink"):
            return items[:limit]
        res = graph("GET", res["@odata.nextLink"])


# ---------- lookups ----------

def _pick(items, wanted, kind):
    """Match by ID, exact name, then partial name (case-insensitive)."""
    w = wanted.lower()
    for test in (lambda i: i["id"] == wanted, lambda i: (i.get("displayName") or "").lower() == w,
                 lambda i: w in (i.get("displayName") or "").lower()):
        found = [i for i in items if test(i)]
        if len(found) == 1:
            return found[0]
        if len(found) > 1:
            names = ", ".join(i.get("displayName", i["id"]) for i in found[:10])
            raise c.ConnectorError(f"Several {kind}s match '{wanted}': {names}.", "Use the exact name or the ID.")
    raise c.ConnectorError(f"No {kind} matches '{wanted}'.", f"List them with the '{kind}s' command.")


def find_team(name):
    return _pick(graph("GET", "/me/joinedTeams").get("value", []), name, "team")


def find_channel(team_id, name):
    return _pick(graph("GET", f"/teams/{team_id}/channels").get("value", []), name, "channel")


def _message_rows(messages):
    rows = []
    for m in sorted(messages, key=lambda m: m.get("createdDateTime") or "", reverse=True):
        if m.get("messageType") != "message":
            continue
        sender = ((m.get("from") or {}).get("user") or {}).get("displayName") or \
                 ((m.get("from") or {}).get("application") or {}).get("displayName", "")
        text = c.html_to_text((m.get("body") or {}).get("content", "")).replace("\n", " ")
        subject = f"[{m['subject']}] " if m.get("subject") else ""
        rows.append([(m.get("createdDateTime") or "")[:16].replace("T", " "), sender, subject + text, m.get("id")])
    return rows


# ---------- commands ----------

def cmd_test(args):
    did = False
    if c.setting("TEAMS_WEBHOOK_URL"):
        host = urllib.parse.urlsplit(c.setting("TEAMS_WEBHOOK_URL")).netloc   # never print the full URL: it contains a secret
        print(f"Webhook configured (host {host}). 'send' can post to its channel.")
        did = True
    if c.setting("TEAMS_ACCESS_TOKEN") or (c.setting("TEAMS_TENANT_ID") and c.setting("TEAMS_CLIENT_ID")):
        did = True
        if c.setting("TEAMS_ACCESS_TOKEN") or TOKEN_FILE.exists():
            me = graph("GET", "/me")
            print(f"Microsoft Graph OK: signed in as {me.get('displayName')} ({me.get('userPrincipalName')}).")
        else:
            print("Graph settings found, but not signed in. Run 'login' to read messages and post through Graph.")
    if not did:
        raise c.ConnectorError("No Teams settings found.",
                               "Set TEAMS_TENANT_ID and TEAMS_CLIENT_ID (read + post), and/or TEAMS_WEBHOOK_URL (send only).")


def cmd_login(args):
    dc = _oauth("devicecode", {"scope": SCOPES})
    print(dc.get("message") or f"Open {dc['verification_uri']} and enter the code {dc['user_code']}.", flush=True)
    print("Waiting for the sign-in to finish...", file=sys.stderr, flush=True)
    interval = int(dc.get("interval", 5))
    deadline = time.time() + int(dc.get("expires_in", 900))
    while time.time() < deadline:
        time.sleep(interval)
        try:
            tok = _oauth("token", {"grant_type": "urn:ietf:params:oauth:grant-type:device_code", "device_code": dc["device_code"]})
        except c.ConnectorError as e:
            if "authorization_pending" in str(e):
                continue
            if "slow_down" in str(e):
                interval += 5
                continue
            raise
        _save_token(tok)
        print("Signed in. The token is saved in connectors/msteams/.token.json (secret, ignored by git).")
        return
    raise c.ConnectorError("The sign-in code expired before the user finished.", "Run 'login' again.")


def cmd_teams(args):
    rows = [[t["id"], t.get("displayName"), (t.get("description") or "")[:100]]
            for t in graph("GET", "/me/joinedTeams").get("value", [])]
    c.show_table(rows, ["id", "team", "description"], "msteams-teams", limit=200)


def cmd_channels(args):
    team = find_team(args.team)
    rows = [[ch["id"], ch.get("displayName"), ch.get("membershipType", "")]
            for ch in graph("GET", f"/teams/{team['id']}/channels").get("value", [])]
    c.show_table(rows, ["id", "channel", "type"], "msteams-channels", limit=200)


def cmd_messages(args):
    team = find_team(args.team)
    channel = find_channel(team["id"], args.channel)
    msgs = graph_list(f"/teams/{team['id']}/channels/{channel['id']}/messages", args.limit)
    print(f"{team['displayName']} / {channel['displayName']}: latest {len(msgs)} messages")
    c.show_table(_message_rows(msgs), ["time", "from", "text", "message_id"], "msteams-messages", limit=args.limit)


def cmd_replies(args):
    team = find_team(args.team)
    channel = find_channel(team["id"], args.channel)
    base = f"/teams/{team['id']}/channels/{channel['id']}/messages/{args.message_id}"
    root = graph("GET", base)
    replies = graph_list(base + "/replies", args.limit)
    c.show_table(_message_rows([root]) + _message_rows(replies), ["time", "from", "text", "message_id"],
                 "msteams-replies", limit=args.limit + 1)


def cmd_chats(args):
    chats = graph_list("/me/chats", args.limit, {"$expand": "members"})
    rows = []
    for ch in chats:
        members = ", ".join(m.get("displayName") or "" for m in ch.get("members", [])[:6])
        rows.append([ch["id"], ch.get("chatType", ""), ch.get("topic") or members, (ch.get("lastUpdatedDateTime") or "")[:16]])
    c.show_table(rows, ["chat_id", "type", "topic_or_members", "updated"], "msteams-chats", limit=args.limit)


def cmd_chat_messages(args):
    msgs = graph_list(f"/me/chats/{args.chat_id}/messages", args.limit)
    c.show_table(_message_rows(msgs), ["time", "from", "text", "message_id"], "msteams-chat-messages", limit=args.limit)


def cmd_post(args):
    c.require_write(args, "post")
    team = find_team(args.team)
    channel = find_channel(team["id"], args.channel)
    path = f"/teams/{team['id']}/channels/{channel['id']}/messages"
    if args.reply_to:
        path += f"/{args.reply_to}/replies"
    res = graph("POST", path, body={"body": {"contentType": "html", "content": c.markdown_to_html(args.text)}})
    print(f"Posted to {team['displayName']} / {channel['displayName']} (message {res.get('id')}).")


def cmd_chat_send(args):
    c.require_write(args, "chat-send")
    res = graph("POST", f"/chats/{args.chat_id}/messages",
                body={"body": {"contentType": "html", "content": c.markdown_to_html(args.text)}})
    print(f"Sent to chat (message {res.get('id')}).")


def webhook_payload(text, title=None):
    """Adaptive Card message, the format Teams workflow webhooks accept."""
    body = []
    if title:
        body.append({"type": "TextBlock", "text": title, "weight": "Bolder", "size": "Medium", "wrap": True})
    body.append({"type": "TextBlock", "text": text, "wrap": True})
    return {"type": "message", "attachments": [{
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {"$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard", "version": "1.4", "body": body}}]}


def cmd_preview(args):
    print(json.dumps(webhook_payload(args.text, args.title), indent=2))
    print("\n(preview only; nothing was sent)")


def cmd_send(args):
    url = c.need("TEAMS_WEBHOOK_URL")[0]
    if not url.startswith("https://"):
        raise c.ConnectorError("TEAMS_WEBHOOK_URL must start with https://")
    c.require_write(args, "send")
    c.http("POST", url, body=webhook_payload(args.text, args.title))
    print("Message sent.")


def main():
    p = argparse.ArgumentParser(description="Read Teams channels, messages and chats; post messages (posting needs --write).")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("test", help="check settings and sign-in").set_defaults(func=cmd_test)
    sub.add_parser("login", help="sign in once (device code in a browser)").set_defaults(func=cmd_login)
    sub.add_parser("teams", help="list your teams").set_defaults(func=cmd_teams)

    s = sub.add_parser("channels", help="list channels of a team")
    s.add_argument("team", help="team name or ID")
    s.set_defaults(func=cmd_channels)

    s = sub.add_parser("messages", help="latest messages in a channel")
    s.add_argument("team")
    s.add_argument("channel", help="channel name or ID")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_messages)

    s = sub.add_parser("replies", help="a channel message and its replies")
    s.add_argument("team")
    s.add_argument("channel")
    s.add_argument("message_id")
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(func=cmd_replies)

    s = sub.add_parser("chats", help="list your chats")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_chats)

    s = sub.add_parser("chat-messages", help="latest messages in a chat")
    s.add_argument("chat_id")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_chat_messages)

    s = sub.add_parser("post", help="post to a channel through Graph (needs --write)")
    s.add_argument("team")
    s.add_argument("channel")
    s.add_argument("text", help="message (Markdown)")
    s.add_argument("--reply-to", help="message ID to reply to")
    s.add_argument("--write", action="store_true", help="needed; ask the user first")
    s.set_defaults(func=cmd_post)

    s = sub.add_parser("chat-send", help="send to a chat through Graph (needs --write)")
    s.add_argument("chat_id")
    s.add_argument("text", help="message (Markdown)")
    s.add_argument("--write", action="store_true", help="needed; ask the user first")
    s.set_defaults(func=cmd_chat_send)

    for name, func, help_text in (("preview", cmd_preview, "show a webhook message without sending"),
                                  ("send", cmd_send, "send through the webhook (needs --write)")):
        s = sub.add_parser(name, help=help_text)
        s.add_argument("text")
        s.add_argument("--title")
        if name == "send":
            s.add_argument("--write", action="store_true", help="needed; ask the user first")
        s.set_defaults(func=func)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    c.run(main)
