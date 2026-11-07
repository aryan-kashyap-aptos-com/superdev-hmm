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
    passed = counts.get("Verified", 0)
    rate = round(100 * passed / total) if total else 0
    stats = "".join(f'<div class="stat {BADGE[w]}"><b>{counts.get(w, 0)}</b><span>{w}</span></div>' for w in RESULTS)
    title_site = f'<a href="{site}" class="site">{site}</a>' if site else ""
    return """<!doctype html><html><head><meta charset="utf-8"><title>QA report: """ + run + """</title>
<style>
:root{
  --bg:#0a0c12;--card:rgba(255,255,255,.035);--card-hov:rgba(255,255,255,.055);--border:rgba(255,255,255,.09);
  --text:#eef0f4;--dim:#8d93a6;--faint:#5b6177;
  --green:#4ade80;--green-bg:rgba(74,222,128,.12);--green-bd:rgba(74,222,128,.3);
  --red:#f87171;--red-bg:rgba(248,113,113,.12);--red-bd:rgba(248,113,113,.3);
  --amber:#fbbf24;--amber-bg:rgba(251,191,36,.12);--amber-bd:rgba(251,191,36,.3);
  --accent:#7dd3fc;--accent-bg:rgba(125,211,252,.14);--accent-bd:rgba(125,211,252,.35);
  --serif:Georgia,'Iowan Old Style','Palatino Linotype',serif;
  --sans:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;font:15px/1.6 var(--sans);background-color:var(--bg);color:var(--text);
  background-image:radial-gradient(circle at 1px 1px,rgba(255,255,255,.055) 1px,transparent 0);background-size:26px 26px}
a{color:var(--accent)}
.wrap{max-width:860px;margin:0 auto;padding:64px 28px 120px}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);font-weight:600}
h1{font-family:var(--serif);font-weight:400;font-size:34px;line-height:1.25;margin:10px 0 6px;letter-spacing:-.01em}
.site{font-size:16px;text-decoration:none;border-bottom:1px solid var(--accent-bd)}
.meta{color:var(--dim);font-size:13px;margin-top:4px}
.stats{display:flex;gap:12px;margin-top:32px;flex-wrap:wrap}
.stat{flex:1;min-width:120px;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px 20px}
.stat b{display:block;font-family:var(--serif);font-size:30px;font-weight:400;line-height:1}
.stat span{color:var(--dim);font-size:12px;margin-top:4px;display:block}
.stat.ok b{color:var(--green)}.stat.bad b{color:var(--red)}.stat.mid b{color:var(--amber)}.stat.nt b{color:var(--dim)}
.rate{color:var(--dim);font-size:13px;margin-top:14px}
.rate b{color:var(--text);font-weight:600}
hr.rule{border:none;border-top:1px solid var(--border);margin:40px 0 28px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:34px}
.filters button{background:var(--card);border:1px solid var(--border);color:var(--dim);border-radius:999px;
  padding:7px 16px;cursor:pointer;font:inherit;font-size:12.5px;transition:background .15s,color .15s,border-color .15s}
.filters button:hover{color:var(--text);border-color:var(--faint)}
.filters button.on{color:#06222c;background:var(--accent);border-color:var(--accent);font-weight:600}
.task-h{display:flex;align-items:center;gap:10px;margin:40px 0 16px}
.task-h .dot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex:none}
.task-h span{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);font-weight:600}
.ev{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px 20px;margin-bottom:12px}
.ev:hover{background:var(--card-hov)}
.ev-top{display:flex;align-items:flex-start;gap:12px}
.seq{color:var(--faint);font-size:11.5px;flex:none;padding-top:3px;font-variant-numeric:tabular-nums;letter-spacing:.02em}
.ev-body{flex:1;min-width:0}
.txt{font-weight:500;font-size:14.5px}
.txt b{color:var(--accent);font-weight:600}
.msg{color:var(--dim);font-size:13px;margin-top:4px;white-space:pre-wrap;word-break:break-word}
.side{flex:none;display:flex;flex-direction:column;align-items:flex-end;gap:5px}
.badge{font-size:11px;border-radius:999px;padding:4px 11px;border:1px solid;white-space:nowrap}
.badge.ok{background:var(--green-bg);color:var(--green);border-color:var(--green-bd)}
.badge.bad{background:var(--red-bg);color:var(--red);border-color:var(--red-bd)}
.badge.mid{background:var(--amber-bg);color:var(--amber);border-color:var(--amber-bd)}
.badge.nt{background:var(--card);color:var(--dim);border-color:var(--border)}
.ms{color:var(--faint);font-size:11px;font-variant-numeric:tabular-nums}
.thumbs{margin-top:14px;display:flex;gap:10px;flex-wrap:wrap}
.thumb-wrap{display:flex;flex-direction:column;gap:5px}
.thumb-wrap img{width:260px;height:170px;object-fit:cover;object-position:top;border-radius:10px;
  border:1px solid var(--border);cursor:zoom-in;display:block;transition:border-color .15s}
.thumb-wrap img:hover{border-color:var(--accent-bd)}
.thumb-cap{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
details{margin-top:14px}
summary{cursor:pointer;color:var(--accent);font-size:12.5px;user-select:none;list-style:none}
summary::-webkit-details-marker{display:none}
summary:before{content:'\\25B8';display:inline-block;margin-right:6px;transition:transform .15s}
details[open] summary:before{transform:rotate(90deg)}
.nettbl{margin-top:10px;background:rgba(0,0,0,.25);border:1px solid var(--border);border-radius:12px;overflow:hidden}
table{border-collapse:collapse;font-size:12px;width:100%;table-layout:fixed;font-family:ui-monospace,Consolas,monospace}
th{text-align:left;font:600 10px/1 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--faint);
  padding:9px 10px;border-bottom:1px solid var(--border)}
td{padding:6px 10px;border-bottom:1px solid rgba(255,255,255,.04);color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
tr:last-child td{border-bottom:none}
td.m{width:52px}td.s{width:46px}td.t{width:84px}td.ms{width:70px}
.netbad{color:var(--red)}
.empty{color:var(--dim);padding:40px 0;text-align:center;font-size:14px}
</style></head><body>
<div class="wrap">
<div class="eyebrow">QA report</div>
<h1>""" + run + """</h1>
""" + (f'<div class="meta">{title_site}</div>' if site else "") + """
<div class="meta">Started """ + started + " &middot; finished " + finished + f" &middot; {total} recorded" + """</div>
<div class="stats">""" + stats + f"""</div>
<div class="rate">Pass rate: <b>{rate}%</b> ({passed} of {total} verified)</div>
""" + """<hr class="rule">
<div class="filters" id="filters"></div>
<div id="list"></div>
</div>
<script>
const EVENTS = """ + json.dumps(events) + """;
const BADGE = """ + json.dumps(BADGE) + """;
const esc = s => String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let activeFilter = null;
function netTable(rows){
  if(!rows || !rows.length) return '';
  const body = rows.map(r=>`<tr><td class="m">${esc(r.m)}</td><td class="s ${r.f||(r.s&&r.s>=400)?'netbad':''}">${r.f?'ERR':esc(r.s??'...')}</td><td class="t">${esc(r.t)}</td><td class="ms">${r.ms!=null?r.ms+' ms':''}</td><td title="${esc(r.u)}">${esc(r.u)}</td></tr>`).join('');
  return `<details><summary>${rows.length} network call${rows.length===1?'':'s'}</summary><div class="nettbl"><table>
    <tr><th class="m">Method</th><th class="s">Status</th><th class="t">Type</th><th class="ms">Time</th><th>URL</th></tr>
    ${body}</table></div></details>`;
}
function render(){
  const list = document.getElementById('list');
  let html = '', lastTask = null;
  for (const e of EVENTS){
    if (activeFilter && e.result !== activeFilter) continue;
    const task = e.task || '(no task)';
    if (task !== lastTask){ html += `<div class="task-h"><span class="dot"></span><span>${esc(task)}</span></div>`; lastTask = task; }
    const cls = BADGE[e.result] || 'nt';
    const shots = Array.isArray(e.screenshot) ? e.screenshot : (e.screenshot ? [e.screenshot] : []);
    html += `<div class="ev"><div class="ev-top"><div class="seq">#${String(e.seq).padStart(3,'0')}</div><div class="ev-body">
      <div class="txt">${e.case_id ? `<b>${esc(e.case_id)}</b> &middot; ` : ''}${esc(e.text)}</div>
      ${e.msg ? `<div class="msg">${esc(e.msg)}</div>` : ''}
      ${shots.length ? `<div class="thumbs">${shots.map(s=>`<div class="thumb-wrap"><img src="${esc(s)}" onclick="window.open(this.src)"><span class="thumb-cap">Click to enlarge</span></div>`).join('')}</div>` : ''}
      ${netTable(e.net)}
      </div>
      <div class="side">${e.result ? `<div class="badge ${cls}">${esc(e.result)}</div>` : ''}${e.ms!=null?`<span class="ms">${e.ms} ms</span>`:''}</div>
    </div></div>`;
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
