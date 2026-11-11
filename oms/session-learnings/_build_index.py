"""One-off builder: refresh transcript-index.json from ConnectorSuite agent transcripts."""
import json
import re
from pathlib import Path

TRANSCRIPT_ROOT = Path(
    r"C:\Users\akashyap\.cursor\projects\c-PROD-ConnectorSuite\agent-transcripts"
)
OUT = Path(__file__).resolve().parent

TOPIC_RULES = [
    ("pod2dev-ec2", re.compile(r"pod2|webserver_setup|dfs|oms_ec2|terminate|toronado", re.I)),
    ("iis-app-pool", re.compile(r"\biis\b|app pool|recycl", re.I)),
    ("ebs-disk", re.compile(r"\bebs\b|disk space|productExports|sh-cnt|content server", re.I)),
    ("mq-ssm", re.compile(r"\bssm\b|rabbit|amazon mq|vhost|force.new.deployment", re.I)),
    ("harness", re.compile(r"harness|git tag|ecr publish", re.I)),
    ("crm", re.compile(r"\bcrm\b|CRMAPI", re.I)),
    ("simfa-lambda", re.compile(r"simfa|lambda deploy|snowpa|reconciliation", re.I)),
    ("rds-sso", re.compile(r"\brds\b|sso|oms_aws_rds", re.I)),
    ("batch-scheduler", re.compile(r"batch job|servicemanagerscheduler|eventbridge|15.minute", re.I)),
    ("odx-feeds", re.compile(r"\bodx\b|omsfeed|feed monitor|omsfeedsqueuedorder", re.I)),
]


def user_query(obj: dict) -> str:
    text = ""
    for part in (obj.get("message") or {}).get("content") or []:
        if part.get("type") == "text":
            text += part.get("text", "")
    m = re.search(r"<user_query>\s*(.*?)(?:</user_query>|$)", text, re.S)
    q = (m.group(1) if m else text).strip()
    return re.sub(r"\s+", " ", q)[:400]


def main() -> None:
    index = []
    for fp in sorted(TRANSCRIPT_ROOT.rglob("*.jsonl")):
        tid = fp.stem
        q = ""
        for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("role") == "user" and not q:
                q = user_query(obj)
        topics = [name for name, rx in TOPIC_RULES if rx.search(q)]
        index.append(
            {
                "transcriptId": tid,
                "firstUserQuery": q,
                "topics": topics,
                "sourcePath": str(fp),
            }
        )
    (OUT / "transcript-index.json").write_text(
        json.dumps(index, indent=2), encoding="utf-8"
    )
    print(f"wrote {len(index)} transcript entries")


if __name__ == "__main__":
    main()
