"""Builds one standalone report.html from everything recorded during a run (see record.py): every ad hoc
command, every scenario step, every crawled page, in the order it really happened, each with a sequential
test id, its own observation, timing, a screenshot where one was taken, and the network calls it made.

Open the file directly (no server, no Chrome, no Playwright needed) any time after the run is over - that
is the point of it: a reviewable record of the whole session, for yourself later or for showing someone else.
Every entry is collapsible (open by default only for Issue found / Could not verify, so a long run reads as
a short list of what went wrong plus a lot you can expand into if you want to).
"""
import json
import platform
from pathlib import Path

import core
import record

RESULTS = ["Verified", "Issue found", "Could not verify", "Not tested"]
BADGE = {"Verified": "ok", "Issue found": "bad", "Could not verify": "mid", "Not tested": "nt"}
OPEN_BY_DEFAULT = {"Issue found", "Could not verify"}


def build(run, out_path=None):
    events = record.read_events(run)
    if not events:
        raise core.c.ConnectorError(
            f"No recorded events for run '{run}' yet.",
            "Events are written by ad hoc commands, `play`, and `crawl` while this run is active (--run "
            f"{run}, or make it the active run with qa-tester/test-run.py use).")
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
    env_bits = [f"Site: {site}" if site else None, f"Host: {platform.system()} {platform.release()}", "Runner: local"]
    env_line = " &middot; ".join(b for b in env_bits if b)
    return """<!doctype html><html><head><meta charset="utf-8"><title>QA report: """ + run + """</title>
<script>(function(){try{var s=localStorage.getItem('qa_report_theme');
var sysLight=window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches;
document.documentElement.dataset.theme=s||(sysLight?'light':'dark');}catch(e){}})();</script>
<style>
:root{
  --bg:#0a0c12;--card:rgba(255,255,255,.035);--card-hov:rgba(255,255,255,.055);--border:rgba(255,255,255,.09);
  --text:#eef0f4;--dim:#8d93a6;--faint:#5b6177;--dot:rgba(255,255,255,.055);--code-bg:rgba(0,0,0,.25);
  --shadow:none;--toggle-bg:rgba(255,255,255,.06);--hairline:rgba(255,255,255,.04);
  --green:#4ade80;--green-bg:rgba(74,222,128,.12);--green-bd:rgba(74,222,128,.3);
  --red:#f87171;--red-bg:rgba(248,113,113,.12);--red-bd:rgba(248,113,113,.3);
  --amber:#fbbf24;--amber-bg:rgba(251,191,36,.12);--amber-bd:rgba(251,191,36,.3);
  --accent:#7dd3fc;--accent-bg:rgba(125,211,252,.14);--accent-bd:rgba(125,211,252,.35);--accent-ink:#06222c;
  --serif:Georgia,'Iowan Old Style','Palatino Linotype',serif;
  --sans:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
:root[data-theme="light"]{
  --bg:#f6f6f8;--card:#ffffff;--card-hov:#fbfbfd;--border:rgba(16,24,40,.09);
  --text:#161922;--dim:#5c6273;--faint:#9499a8;--dot:rgba(16,24,40,.07);--code-bg:rgba(16,24,40,.035);
  --shadow:0 1px 2px rgba(16,24,40,.04),0 2px 8px rgba(16,24,40,.06);--toggle-bg:#ffffff;--hairline:rgba(16,24,40,.06);
  --green:#15803d;--green-bg:rgba(21,128,61,.1);--green-bd:rgba(21,128,61,.28);
  --red:#c0211d;--red-bg:rgba(192,33,29,.09);--red-bd:rgba(192,33,29,.28);
  --amber:#b45309;--amber-bg:rgba(180,83,9,.1);--amber-bd:rgba(180,83,9,.28);
  --accent:#0e7490;--accent-bg:rgba(14,116,144,.1);--accent-bd:rgba(14,116,144,.3);--accent-ink:#ffffff;
}
*{box-sizing:border-box}
body{margin:0;font:15px/1.6 var(--sans);background-color:var(--bg);color:var(--text);
  background-image:radial-gradient(circle at 1px 1px,var(--dot) 1px,transparent 0);background-size:26px 26px;
  transition:background-color .25s ease,color .25s ease}
a{color:var(--accent)}
.theme-toggle{position:fixed;top:24px;right:28px;width:40px;height:40px;border-radius:50%;z-index:50;
  background:var(--toggle-bg);border:1px solid var(--border);box-shadow:var(--shadow);cursor:pointer;
  display:flex;align-items:center;justify-content:center}
.theme-toggle:hover{border-color:var(--faint)}
.theme-toggle svg{position:absolute;width:18px;height:18px;color:var(--text);
  transition:opacity .25s ease,transform .4s cubic-bezier(.4,0,.2,1)}
.theme-toggle .sun{opacity:1;transform:rotate(0) scale(1)}
.theme-toggle .moon{opacity:0;transform:rotate(90deg) scale(.5)}
:root[data-theme="light"] .theme-toggle .sun{opacity:0;transform:rotate(-90deg) scale(.5)}
:root[data-theme="light"] .theme-toggle .moon{opacity:1;transform:rotate(0) scale(1)}
.wrap{max-width:860px;margin:0 auto;padding:64px 28px 120px}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);font-weight:600}
h1{font-family:var(--serif);font-weight:400;font-size:34px;line-height:1.25;margin:10px 0 6px;letter-spacing:-.01em}
.site{font-size:16px;text-decoration:none;border-bottom:1px solid var(--accent-bd)}
.meta{color:var(--dim);font-size:13px;margin-top:4px}
.env{color:var(--faint);font-size:12px;margin-top:10px}
.stats{display:flex;gap:12px;margin-top:32px;flex-wrap:wrap}
.stat{flex:1;min-width:120px;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px 20px;
  box-shadow:var(--shadow);transition:background-color .25s ease,border-color .25s ease}
.stat b{display:block;font-family:var(--serif);font-size:30px;font-weight:400;line-height:1}
.stat span{color:var(--dim);font-size:12px;margin-top:4px;display:block}
.stat.ok b{color:var(--green)}.stat.bad b{color:var(--red)}.stat.mid b{color:var(--amber)}.stat.nt b{color:var(--dim)}
.rate{color:var(--dim);font-size:13px;margin-top:14px}
.rate b{color:var(--text);font-weight:600}
hr.rule{border:none;border-top:1px solid var(--border);margin:40px 0 28px}
.toolbar{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:14px}
.filters{display:flex;gap:8px;flex-wrap:wrap}
.filters button{background:var(--card);border:1px solid var(--border);color:var(--dim);border-radius:999px;
  padding:7px 16px;cursor:pointer;font:inherit;font-size:12.5px;transition:background .15s,color .15s,border-color .15s}
.filters button:hover{color:var(--text);border-color:var(--faint)}
.filters button.on{color:var(--accent-ink);background:var(--accent);border-color:var(--accent);font-weight:600}
.tagrow{display:flex;gap:8px;flex-wrap:wrap;margin:-20px 0 34px}
.tagrow button{background:transparent;border:1px dashed var(--border);color:var(--faint);border-radius:999px;
  padding:5px 13px;cursor:pointer;font:inherit;font-size:11.5px}
.tagrow button.on{color:var(--accent);border-color:var(--accent-bd);border-style:solid;background:var(--accent-bg)}
.expandall{background:none;border:none;color:var(--faint);cursor:pointer;font:inherit;font-size:12px;text-decoration:underline;text-underline-offset:2px}
.expandall:hover{color:var(--accent)}
.task-h{display:flex;align-items:center;gap:10px;margin:40px 0 16px}
.task-h .dot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex:none}
.task-h span{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);font-weight:600}
.ev{background:var(--card);border:1px solid var(--border);border-radius:16px;margin-bottom:12px;overflow:hidden;
  box-shadow:var(--shadow);transition:background-color .25s ease,border-color .25s ease}
.ev:hover{background:var(--card-hov)}
.ev-top{display:flex;align-items:flex-start;gap:12px;padding:18px 20px;cursor:pointer;user-select:none}
.chev{color:var(--faint);font-size:11px;flex:none;padding-top:5px;transition:transform .15s}
.ev.open .chev{transform:rotate(90deg)}
.seq{color:var(--faint);font-size:11.5px;flex:none;padding-top:3px;font-variant-numeric:tabular-nums;letter-spacing:.02em}
.ev-head{flex:1;min-width:0}
.txt{font-weight:500;font-size:14.5px}
.txt b{color:var(--accent);font-weight:600}
.chips{display:flex;gap:6px;margin-top:7px;flex-wrap:wrap}
.chip{font-size:10px;letter-spacing:.04em;text-transform:uppercase;color:var(--faint);border:1px solid var(--border);
  border-radius:999px;padding:2px 8px}
.msg{color:var(--dim);font-size:13px;margin-top:4px;white-space:pre-wrap;word-break:break-word}
.side{flex:none;display:flex;flex-direction:column;align-items:flex-end;gap:5px}
.badge{font-size:11px;border-radius:999px;padding:4px 11px;border:1px solid;white-space:nowrap}
.badge.ok{background:var(--green-bg);color:var(--green);border-color:var(--green-bd)}
.badge.bad{background:var(--red-bg);color:var(--red);border-color:var(--red-bd)}
.badge.mid{background:var(--amber-bg);color:var(--amber);border-color:var(--amber-bd)}
.badge.nt{background:var(--card);color:var(--dim);border-color:var(--border)}
.ms{color:var(--faint);font-size:11px;font-variant-numeric:tabular-nums}
.ev-detail{display:none;padding:0 20px 20px 46px}
.ev.open .ev-detail{display:block}
.thumbs{margin-top:4px;display:flex;gap:10px;flex-wrap:wrap}
.thumb-wrap{display:flex;flex-direction:column;gap:5px}
.thumb-wrap img{width:260px;height:170px;object-fit:cover;object-position:top;border-radius:10px;
  border:1px solid var(--border);cursor:zoom-in;display:block;transition:border-color .15s}
.thumb-wrap img:hover{border-color:var(--accent-bd)}
.thumb-cap{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
details{margin-top:4px}
summary{cursor:pointer;color:var(--accent);font-size:12.5px;user-select:none;list-style:none}
summary::-webkit-details-marker{display:none}
summary:before{content:'\\25B8';display:inline-block;margin-right:6px;transition:transform .15s}
details[open] summary:before{transform:rotate(90deg)}
.nettbl{margin-top:10px;background:var(--code-bg);border:1px solid var(--border);border-radius:12px;overflow:hidden}
table{border-collapse:collapse;font-size:12px;width:100%;table-layout:fixed;font-family:ui-monospace,Consolas,monospace}
th{text-align:left;font:600 10px/1 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--faint);
  padding:9px 10px;border-bottom:1px solid var(--border)}
td{padding:6px 10px;border-bottom:1px solid var(--hairline);color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
tr:last-child td{border-bottom:none}
td.m{width:52px}td.s{width:46px}td.t{width:84px}td.ms{width:70px}
.netbad{color:var(--red)}
.empty{color:var(--dim);padding:40px 0;text-align:center;font-size:14px}
</style></head><body>
<button class="theme-toggle" id="themeToggle" title="Switch between dark and light" aria-label="Switch between dark and light">
<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
<svg class="moon" viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
</button>
<div class="wrap">
<div class="eyebrow">QA report</div>
<h1>""" + run + """</h1>
""" + (f'<div class="meta">{title_site}</div>' if site else "") + """
<div class="meta">Started """ + started + " &middot; finished " + finished + f" &middot; {total} recorded" + """</div>
<div class="env">""" + env_line + """</div>
<div class="stats">""" + stats + f"""</div>
<div class="rate">Pass rate: <b>{rate}%</b> ({passed} of {total} verified)</div>
""" + """<hr class="rule">
<div class="toolbar">
  <div class="filters" id="filters"></div>
  <button class="expandall" id="expandall">Expand all</button>
</div>
<div class="tagrow" id="tagrow"></div>
<div id="list"></div>
</div>
<script>
const EVENTS = """ + json.dumps(events) + """;
const BADGE = """ + json.dumps(BADGE) + """;
const OPEN_BY_DEFAULT = """ + json.dumps(sorted(OPEN_BY_DEFAULT)) + """;
const esc = s => String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let activeFilter = null, activeTag = null, allOpen = false;
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
    if (activeTag && !(e.tags||[]).includes(activeTag)) continue;
    const task = e.task || '(no task)';
    if (task !== lastTask){ html += `<div class="task-h"><span class="dot"></span><span>${esc(task)}</span></div>`; lastTask = task; }
    const cls = BADGE[e.result] || 'nt';
    const shots = Array.isArray(e.screenshot) ? e.screenshot : (e.screenshot ? [e.screenshot] : []);
    const hasDetail = !!(e.msg || shots.length || (e.net && e.net.length));
    const openDefault = allOpen || OPEN_BY_DEFAULT.includes(e.result);
    const tags = (e.tags||[]).map(t=>`<span class="chip">${esc(t)}</span>`).join('');
    html += `<div class="ev ${hasDetail && openDefault ? 'open':''}" data-seq="${e.seq}">
      <div class="ev-top" onclick="${hasDetail ? `toggle(${e.seq})` : ''}">
        <span class="chev">${hasDetail ? '\\u25B8' : ''}</span>
        <div class="seq">#${String(e.seq).padStart(3,'0')}</div>
        <div class="ev-head">
          <div class="txt">${e.case_id ? `<b>${esc(e.case_id)}</b> &middot; ` : ''}${esc(e.text)}</div>
          ${tags ? `<div class="chips">${tags}</div>` : ''}
        </div>
        <div class="side">${e.result ? `<div class="badge ${cls}">${esc(e.result)}</div>` : ''}${e.ms!=null?`<span class="ms">${e.ms} ms</span>`:''}</div>
      </div>
      ${hasDetail ? `<div class="ev-detail">
        ${e.msg ? `<div class="msg">${esc(e.msg)}</div>` : ''}
        ${shots.length ? `<div class="thumbs">${shots.map(s=>`<div class="thumb-wrap"><img src="${esc(s)}" onclick="event.stopPropagation();window.open(this.src)"><span class="thumb-cap">Click to enlarge</span></div>`).join('')}</div>` : ''}
        ${netTable(e.net)}
      </div>` : ''}
    </div>`;
  }
  list.innerHTML = html || '<div class="empty">No events match this filter.</div>';
}
function toggle(seq){
  const el = document.querySelector(`.ev[data-seq="${seq}"]`);
  if (el) el.classList.toggle('open');
}
document.getElementById('expandall').onclick = () => {
  allOpen = !allOpen;
  document.getElementById('expandall').textContent = allOpen ? 'Collapse all' : 'Expand all';
  render();
};
function buildFilters(){
  const counts = {};
  for (const e of EVENTS) if (e.result) counts[e.result] = (counts[e.result]||0) + 1;
  const f = document.getElementById('filters');
  const mk = (label, val) => {
    const b = document.createElement('button');
    b.textContent = label;
    b.onclick = () => { activeFilter = val; [...f.children].forEach(x=>x.classList.toggle('on', x===b)); render(); };
    return b;
  };
  const all = mk(`All ${EVENTS.length}`, null);
  f.appendChild(all);
  for (const w of Object.keys(BADGE)) if (counts[w]) f.appendChild(mk(`${w} ${counts[w]}`, w));
  all.classList.add('on');
}
function buildTags(){
  const counts = {};
  for (const e of EVENTS) for (const t of (e.tags||[])) counts[t] = (counts[t]||0) + 1;
  const names = Object.keys(counts);
  if (!names.length) return;
  const row = document.getElementById('tagrow');
  for (const t of names.sort()){
    const b = document.createElement('button');
    b.textContent = `#${t} ${counts[t]}`;
    b.onclick = () => { activeTag = activeTag === t ? null : t; [...row.children].forEach(x=>x.classList.toggle('on', x===b && activeTag===t)); render(); };
    row.appendChild(b);
  }
}
buildFilters(); buildTags(); render();
document.getElementById('themeToggle').onclick = () => {
  const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('qa_report_theme', next); } catch (e) {}
};
</script></body></html>"""
