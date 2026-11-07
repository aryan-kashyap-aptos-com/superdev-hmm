"""Builds one standalone report.html from everything recorded during a run (see record.py): every ad hoc
command, every scenario step, every crawled page, in the order it really happened, each with a sequential
test id, its own observation, timing, a screenshot where one was taken, and the network calls it made.

Open the file directly (no server, no Chrome, no Playwright needed) any time after the run is over - that
is the point of it: a reviewable record of the whole session, for yourself later or for showing someone else.
"""
import json
from pathlib import Path

import core
import record

RESULTS = ["Verified", "Issue found", "Could not verify", "Not tested"]
BADGE = {"Verified": "ok", "Issue found": "bad", "Could not verify": "mid", "Not tested": "nt"}


def build(run, out_path=None):
    events = record.read_events(run)
    if not events:
        raise core.c.ConnectorError(
            f"No recorded events for run '{run}' yet.",
            "Events are written by ad hoc commands, `play`, and `crawl` while this run is active (--run "
            f"{run}, or make it the active run with qa-tester/test-run.py use).")
    tasks, seen = [], set()
    for e in events:
        t = e.get("task") or "(no task)"
        if t not in seen:
            seen.add(t)
            tasks.append(t)
    counts = {}
    for e in events:
        if e.get("result"):
            counts[e["result"]] = counts.get(e["result"], 0) + 1
    site = None
    try:
        site = (core.run_login(run) or {}).get("site")
    except Exception:
        pass
    out_path = Path(out_path) if out_path else core.QA / "runs" / run / "report.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_html(run, site, events, counts), encoding="utf-8")
    return out_path, events, counts


def _html(run, site, events, counts):
    total = len(events)
    started, finished = events[0]["ts"], events[-1]["ts"]
    summary = "".join(f'<div class="stat {BADGE[w]}"><b>{counts.get(w, 0)}</b><span>{w}</span></div>' for w in RESULTS)
    title_site = f" &middot; {site}" if site else ""
    return """<!doctype html><html><head><meta charset="utf-8"><title>QA report: """ + run + """</title>
<style>
:root{--bg:#171a26;--top:#1f2233;--line:#2c3047;--text:#d6d9e6;--dim:#7c829b;--green:#3fb950;--red:#f85149;--amber:#d9a521;--blue:#58a6ff}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 "Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--text)}
header{background:var(--top);border-bottom:1px solid var(--line);padding:24px 32px;position:sticky;top:0;z-index:2}
h1{margin:0;font-size:20px;font-weight:600}.meta{color:var(--dim);font-size:13px;margin-top:6px}
.stats{display:flex;gap:16px;margin-top:16px;flex-wrap:wrap}
.stat{background:#262a3f;border-radius:8px;padding:10px 18px;min-width:120px}
.stat b{display:block;font-size:22px}.stat span{color:var(--dim);font-size:12px}
.stat.ok b{color:var(--green)}.stat.bad b{color:var(--red)}.stat.mid b{color:var(--amber)}.stat.nt b{color:var(--dim)}
main{max-width:1100px;margin:0 auto;padding:20px 32px 100px}
.filters{display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap}
.filters button{background:#262a3f;border:1px solid var(--line);color:var(--dim);border-radius:6px;padding:6px 14px;cursor:pointer;font:inherit;font-size:12px}
.filters button.on{color:#fff;background:var(--blue);border-color:var(--blue)}
.task-h{margin:30px 0 10px;font-size:15px;font-weight:600;color:var(--text);border-bottom:1px solid var(--line);padding-bottom:8px}
.ev{display:flex;gap:14px;padding:12px 0;border-bottom:1px solid var(--line);align-items:flex-start}
.seq{color:var(--dim);font-size:12px;flex:none;width:52px;padding-top:2px;font-variant-numeric:tabular-nums}
.body{flex:1;min-width:0}.txt{font-weight:500}.msg{color:var(--dim);font-size:13px;margin-top:3px;white-space:pre-wrap;word-break:break-word}
.badge{font-size:11px;border-radius:4px;padding:3px 8px;flex:none;height:fit-content}
.badge.ok{background:#1b3a24;color:var(--green)}.badge.bad{background:#3a1f1e;color:var(--red)}
.badge.mid{background:#3a2f12;color:var(--amber)}.badge.nt{background:#262a3f;color:var(--dim)}
.ms{color:var(--dim);font-size:11px;flex:none;width:64px;text-align:right;padding-top:4px;font-variant-numeric:tabular-nums}
.thumb{margin-top:10px}.thumb img{width:240px;height:160px;object-fit:cover;object-position:top;border-radius:6px;border:1px solid var(--line);cursor:zoom-in;display:block}
table{border-collapse:collapse;margin-top:8px;font-size:12px;width:100%;table-layout:fixed}
td{padding:3px 10px 3px 0;border-bottom:1px solid var(--line);color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
td.m{width:50px}td.s{width:42px}td.t{width:80px}td.ms{width:70px}
.netbad{color:var(--red)}
details{margin-top:8px}summary{cursor:pointer;color:var(--blue);font-size:12px;user-select:none}
.empty{color:var(--dim);padding:30px 0}
</style></head><body>
<header>
<h1>QA report: """ + run + title_site + """</h1>
<div class="meta">Started """ + started + " &middot; finished " + finished + f" &middot; {total} recorded" + """</div>
<div class="stats">""" + summary + """</div>
</header>
<main>
<div class="filters" id="filters"></div>
<div id="list"></div>
</main>
<script>
const EVENTS = """ + json.dumps(events) + """;
const BADGE = """ + json.dumps(BADGE) + """;
const esc = s => String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let activeFilter = null;
function netTable(rows){
  if(!rows || !rows.length) return '';
  const body = rows.map(r=>`<tr><td class="m">${esc(r.m)}</td><td class="s ${r.f||(r.s&&r.s>=400)?'netbad':''}">${r.f?'ERR':esc(r.s??'...')}</td><td class="t">${esc(r.t)}</td><td class="ms">${r.ms!=null?r.ms+' ms':''}</td><td title="${esc(r.u)}">${esc(r.u)}</td></tr>`).join('');
  return `<details><summary>${rows.length} network call(s)</summary><table>${body}</table></details>`;
}
function render(){
  const list = document.getElementById('list');
  let html = '', lastTask = null, shown = 0;
  for (const e of EVENTS){
    if (activeFilter && e.result !== activeFilter) continue;
    shown++;
    const task = e.task || '(no task)';
    if (task !== lastTask){ html += `<div class="task-h">${esc(task)}</div>`; lastTask = task; }
    const cls = BADGE[e.result] || 'nt';
    const shots = Array.isArray(e.screenshot) ? e.screenshot : (e.screenshot ? [e.screenshot] : []);
    html += `<div class="ev"><div class="seq">#${String(e.seq).padStart(3,'0')}</div><div class="body">
      <div class="txt">${esc(e.case_id ? e.case_id + ': ' : '')}${esc(e.text)}</div>
      ${e.msg ? `<div class="msg">${esc(e.msg)}</div>` : ''}
      ${shots.length ? `<div class="thumb" style="display:flex;gap:8px;flex-wrap:wrap">${shots.map(s=>`<img src="${esc(s)}" title="Click to view full size" onclick="window.open(this.src)">`).join('')}</div>` : ''}
      ${netTable(e.net)}
      </div>
      ${e.result ? `<div class="badge ${cls}">${esc(e.result)}</div>` : '<div style="width:0"></div>'}
      <div class="ms">${e.ms!=null?e.ms+' ms':''}</div>
    </div>`;
  }
  list.innerHTML = html || '<div class="empty">No events match this filter.</div>';
}
function buildFilters(){
  const counts = {};
  for (const e of EVENTS) if (e.result) counts[e.result] = (counts[e.result]||0) + 1;
  const f = document.getElementById('filters');
  const mk = (label, val) => {
    const b = document.createElement('button');
    b.textContent = label; b.dataset.val = val === null ? '' : val;
    b.onclick = () => { activeFilter = val; [...f.children].forEach(x=>x.classList.toggle('on', x===b)); render(); };
    return b;
  };
  const all = mk(`All ${EVENTS.length}`, null);
  f.appendChild(all);
  for (const w of Object.keys(BADGE)) if (counts[w]) f.appendChild(mk(`${w} ${counts[w]}`, w));
  all.classList.add('on');
}
buildFilters(); render();
</script></body></html>"""
