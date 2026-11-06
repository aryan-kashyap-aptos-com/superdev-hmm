# Connector: ec2-ssm

## When to use

To look at AWS EC2 servers without SSH: check disk space, services, processes, recent log lines, configuration files.
Works for Linux (shell) and Windows (PowerShell) servers that have the SSM agent.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill it in.
3. Log in to AWS the way you normally do, then run `python connectors/ec2-ssm/run.py test`.

## Commands

| Command | What it does |
|---------|--------------|
| `test` | Shows the AWS account and how many servers SSM can reach. |
| `list [--filter TEXT]` | Lists servers: ID, Name tag, SSM status, platform, IP. |
| `run <id-or-name> "<command>"` | Runs a read-only command and prints its output. |
| `run <id-or-name> "<command>" --write` | Runs any command. Needs the user's permission. |

## Read-only mode

Without `--write`, the script allows only commands that read:

- **Linux:** `cat`, `tail`, `head`, `ls`, `df`, `du`, `free`, `ps`, `grep`, `find` (without `-delete` / `-exec`), `top -b`, `journalctl`, `ss`, `systemctl status`, `docker ps`, `docker logs`, and similar. Pipes (`|`) between allowed commands are fine.
- **Windows (PowerShell):** cmdlets with a read verb (`Get-`, `Test-`, `Select-`, `Where-`, `Sort-`, `Format-`, `Measure-`, `Group-`, `ConvertTo-`, `ForEach-`), common aliases (`gci`, `gc`, `ls`, `ps`, `select`, `where`, `%`, `?`), and `ipconfig`, `netstat`, `tasklist`, `systeminfo`.
  Parentheses, script blocks `{ }`, and hashtables `@{ }` are fine: the script checks every command inside them too.
- **Never allowed in read-only mode:** `;`, `&&`, `&`, `>`, `<`, backticks, `$( )`, `::` (static .NET calls), and method calls that change things (for example `.Kill()`, `.Delete()`). Safe string methods like `.StartsWith()` are fine.

To allow more read-only commands, the user can add them to `EC2_SSM_EXTRA_READ_COMMANDS` in `.env` (comma-separated).

## Which AWS login to use (SSO)

`list` and `run` only see the account and region of the active AWS login. For another account, run with `AWS_PROFILE=<profile>` in front.
If the login expired, see "Which AWS login to use (SSO)" in `connectors/aws-rds/GUIDE.md`.

## Tested on real servers

- Linux: `uptime` ran fine. Windows: `Get-Service | Where-Object { $_.Status -eq 'Running' } | Select-Object -First 3 Name,Status` ran fine.
- Write one pipeline, not two commands joined by `;`. In read-only mode `;` is refused by design.
- Check the guard with the self-test (`python tests/selftest.py`), not by sending blocked commands to a real server.

## Rules

1. Run `list` first to find the right server. Check the name: production servers need extra care.
2. Before `--write`: tell the user the server, the exact command, and what it will change. Wait for "yes".
3. Never use commands that wait forever (`tail -f`, `top` without `-b -n 1`). The command stops at `--timeout`.
4. Limit output: `tail -n 100`, `Select-Object -First 50`, `grep` for the lines you need.
5. Never print files that hold secrets (`.env`, key files, credential stores).

## Examples

```
python connectors/ec2-ssm/run.py list --filter web
python connectors/ec2-ssm/run.py run web-01 "df -h"
python connectors/ec2-ssm/run.py run web-01 "journalctl -u nginx --since '1 hour ago' --no-pager | tail -n 100"
python connectors/ec2-ssm/run.py run i-0abc123 "Get-Service | Where-Object Status -eq Stopped | Select-Object -First 20"
```
