"""The runner panel: a Cypress-style sidebar docked inside the same window as the page under test.

It shows the test cases and their steps before they run (grey), the one running now (blue),
and each result as it happens (green Verified, red Issue found, amber Could not verify, grey Not tested).
Tabs: Tests, Network (the calls each step made, flashed open after a step that loaded something), and Log
(single commands run by hand). It is only a viewer: if it is missing or breaks, the tests carry on.

It lives inside the page itself, as a same-origin `<iframe srcdoc>` pinned to the right edge, not a second
browser window: one app, one thing to look at. A header button (or `mobile` mode) can collapse it to a
small floating pill, docked top-right (not bottom-right, which is where a site's own chat widget, cookie
banner or back-to-top button usually sits) so it never gets in the way of a narrow layout. The pill still
carries working Desktop/iPhone/Android/Tablet buttons, so switching device never requires reopening the
full panel first; tapping the rest of the pill (the "QA" label) brings the full panel back.
Because a real page reload wipes it, Panel keeps its own copy of everything shown (the plan, every result,
every log line, the network rows) and replays that copy into a freshly (re)injected panel after navigation.

Its Desktop/iPhone/Android/Tablet buttons, and its "Report" button, work live, with no CLI command needed:
a click just sets `window.top.__qa_pending_device` or `window.top.__qa_report_requested`; the background
helper (bridge.py, started by `start`) polls for those and does the actual work (switching device, or
building report.html for the active run and opening it). A plain variable survives being read by many
short-lived connections far more reliably than a CDP-exposed function call, which needs one single
long-lived connection to answer it.
"""
import json

import core

STATUS = {"Verified": "verified", "Issue found": "issue", "Could not verify": "cnv", "Not tested": "nt"}

EXPANDED_CSS = ("position:fixed;right:0;top:0;width:360px;height:100%;border:none;z-index:2147483647;"
                "box-shadow:-2px 0 14px rgba(0,0,0,.35)")
_MINI_BASE = ("position:fixed;right:14px;width:236px;height:36px;border:none;border-radius:20px;"
              "z-index:2147483647;box-shadow:0 2px 12px rgba(0,0,0,.45);background:transparent")
MINI_CSS_TOP = _MINI_BASE + ";top:14px"
MINI_CSS_BOTTOM = _MINI_BASE + ";bottom:14px"

CREATE_JS = """([html, css]) => {
  if (document.getElementById("__qa_panel_frame")) return;
  const f = document.createElement('iframe');
  f.id = "__qa_panel_frame";
  f.style.cssText = css;
  f.srcdoc = html;
  (document.documentElement || document.body).appendChild(f);
}"""

READY_JS = """() => {
  const f = document.getElementById("__qa_panel_frame");
  return !!(f && f.contentWindow && f.contentWindow.qa);
}"""

CALL_JS = """([n, a]) => {
  const f = document.getElementById("__qa_panel_frame");
  if (f && f.contentWindow && f.contentWindow.qa) f.contentWindow.qa[n](...a);
}"""

HTML = """<!doctype html><html><head><meta charset="utf-8"><title>QA Runner</title><style>
:root{
  --bg:#0a0c12;--panel:rgba(255,255,255,.03);--card:rgba(255,255,255,.035);--card-hov:rgba(255,255,255,.06);
  --border:rgba(255,255,255,.09);--text:#eef0f4;--dim:#8d93a6;--faint:#5b6177;
  --green:#4ade80;--green-bg:rgba(74,222,128,.14);--green-bd:rgba(74,222,128,.32);
  --red:#f87171;--red-bg:rgba(248,113,113,.14);--red-bd:rgba(248,113,113,.32);
  --amber:#fbbf24;--amber-bg:rgba(251,191,36,.14);--amber-bd:rgba(251,191,36,.32);
  --accent:#7dd3fc;--accent-bg:rgba(125,211,252,.16);--accent-bd:rgba(125,211,252,.38);
  --serif:Georgia,'Iowan Old Style','Palatino Linotype',serif;
}
*{box-sizing:border-box}html,body{margin:0;height:100%;overflow:hidden}
body{font:13px/1.45 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background-color:var(--bg);color:var(--text);
  background-image:radial-gradient(circle at 1px 1px,rgba(255,255,255,.05) 1px,transparent 0);background-size:22px 22px}
#shell{height:100%;display:flex;flex-direction:column}
body.mini #shell{display:none}#mini{display:none}body.mini #mini{display:flex}
#mini{position:absolute;inset:0;border-radius:20px;background:#12151f;color:var(--text);align-items:center;
  gap:6px;padding:0 8px;cursor:pointer;font-weight:700;font-size:11px;border:1px solid var(--border);user-select:none;
  box-shadow:0 2px 10px rgba(0,0,0,.35)}
#mini .dot{width:8px;height:8px;border-radius:50%;background:var(--faint);flex:none}
#mini.has-issue .dot{background:var(--red)}#mini.has-pending .dot{background:var(--accent)}#mini.all-ok .dot{background:var(--green)}
#mini .minidevs{display:flex;gap:3px}
#mini .minidevs button{background:none;border:1px solid var(--border);color:var(--dim);border-radius:999px;padding:2px 7px;font:inherit;font-size:10px;cursor:pointer}
#mini .minidevs button.on{color:#06222c;background:var(--accent);border-color:var(--accent);font-weight:700}
#mini .label{margin-left:auto;flex:none;color:var(--dim)}
header{position:sticky;top:0;z-index:2;background:var(--panel);backdrop-filter:blur(6px);border-bottom:1px solid var(--border);flex:none}
.head{padding:14px 14px 8px;display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.headtext{min-width:0}
h1{font-family:var(--serif);font-size:16px;margin:0;font-weight:400;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sub{color:var(--dim);font-size:12px;margin-top:3px}
.head-actions{display:flex;gap:6px;flex:none}
#collapseBtn,#reportBtn{background:var(--card);border:1px solid var(--border);color:var(--dim);border-radius:999px;padding:4px 10px;cursor:pointer;flex:none;font-size:12px;font-family:inherit}
#collapseBtn:hover,#reportBtn:hover{color:var(--text);border-color:var(--faint)}
#reportBtn{color:var(--accent);border-color:var(--accent-bd)}
.counts{display:flex;gap:6px;margin-top:10px;font-size:11px;flex-wrap:wrap}
.counts span{background:var(--card);border:1px solid var(--border);border-radius:999px;padding:3px 10px}
.counts b{font-weight:700}
.c-v b{color:var(--green)}.c-i b{color:var(--red)}.c-n b{color:var(--amber)}.c-p b{color:var(--dim)}
.devices{display:flex;gap:5px;padding:10px 14px 0}
.devices button{background:var(--card);border:1px solid var(--border);color:var(--dim);border-radius:999px;padding:4px 11px;font:inherit;font-size:11px;cursor:pointer;transition:background .15s,color .15s,border-color .15s}
.devices button.on{color:#06222c;background:var(--accent);border-color:var(--accent);font-weight:600}
.devices button:hover:not(.on){color:var(--text);border-color:var(--faint)}
nav{display:flex;padding:10px 10px 0;gap:2px}
nav button{background:none;border:0;border-bottom:2px solid transparent;color:var(--dim);padding:7px 10px;font:inherit;font-size:12.5px;cursor:pointer}
nav button.on{color:var(--text);border-color:var(--accent)}
main{flex:1;overflow:auto;min-height:0;padding:10px}
.case{background:var(--card);border:1px solid var(--border);border-radius:12px;margin-bottom:8px;overflow:hidden}
.ct{display:flex;gap:8px;padding:9px 12px;align-items:flex-start;font-weight:600}
.case.running>.ct{background:var(--accent-bg)}
.id{color:var(--faint);font-weight:400;flex:none}
.ico{width:16px;height:16px;flex:none;text-align:center;border-radius:50%;font-size:10px;font-weight:700;line-height:16px}
.pending>.ct .ico,.pending .si{color:var(--faint)}
.running>.ct .ico,.step.running .si{color:var(--accent);background:var(--accent-bg)}
.verified>.ct .ico,.step.verified .si{color:var(--green);background:var(--green-bg)}
.issue>.ct .ico,.step.issue .si{color:var(--red);background:var(--red-bg)}
.cnv>.ct .ico,.step.cnv .si{color:var(--amber);background:var(--amber-bg)}
.nt>.ct .ico,.step.nt .si{color:var(--faint)}
.steps{padding:0 12px 10px 36px}
.step{display:flex;gap:8px;padding:3px 0;color:var(--dim)}
.step.running{color:var(--text);font-weight:600}.step.verified,.step.issue,.step.cnv{color:var(--text)}
.si{width:16px;height:16px;flex:none;text-align:center;border-radius:50%;font-size:10px;line-height:16px}
.ms{margin-left:auto;color:var(--faint);font-size:11px;flex:none;padding-left:6px}
.msg{font-size:12px;margin:2px 0 4px 24px;white-space:pre-wrap;word-break:break-word;color:var(--dim)}
.issue .msg{color:#ffb4ae}.cnv .msg{color:#ffd480}
.spin{display:inline-block;animation:p 1s infinite}@keyframes p{50%{opacity:.25}}
.nettbl{background:rgba(0,0,0,.25);border:1px solid var(--border);border-radius:12px;overflow:hidden;margin:0 2px}
table{width:100%;border-collapse:collapse;font-size:11px;table-layout:fixed;font-family:ui-monospace,Consolas,monospace}
th{text-align:left;font:600 9.5px/1 -apple-system,"Segoe UI",sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);padding:8px 8px;border-bottom:1px solid var(--border)}
td{padding:5px 8px;border-bottom:1px solid rgba(255,255,255,.04);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--dim)}
tr:last-child td{border-bottom:none}
td.m{width:40px}td.s{width:34px}td.t{width:54px}td.ms{width:50px;text-align:right}
.ok{color:var(--green)}.bad{color:var(--red)}.mid{color:var(--amber)}
.log{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:9px 12px;margin-bottom:8px;display:flex;gap:8px}
.log .tm{color:var(--faint);font-size:11px;flex:none}
.empty{color:var(--dim);padding:14px 12px;text-align:center;font-size:12px}
</style></head><body>
<div id="shell"><header><div class="head"><div class="headtext"><h1 id="title">QA Runner</h1><div class="sub" id="sub">Waiting for a scenario. Single commands appear under Log.</div></div>
<div class="head-actions"><button id="reportBtn" title="Build and open the full report.html for this run">Report &#8599;</button>
<button id="collapseBtn" title="Collapse to a small pill">&#10095;&#10095;</button></div></div>
<div class="counts" id="counts"></div>
<div class="devices" id="devices" title="Resize the real window to a phone/tablet, or back">
<button data-d="desktop" class="on">Desktop</button><button data-d="iphone">iPhone</button><button data-d="android">Android</button><button data-d="tablet">Tablet</button></div>
<nav><button data-tab="tests" class="on">Tests</button><button data-tab="network">Network</button><button data-tab="log">Log</button></nav></header>
<main><section id="tests"><div class="empty">No test cases yet.</div></section>
<section id="network" hidden><div class="nettbl"><table><tr><th class="m">Method</th><th class="s">Status</th><th class="t">Type</th><th>URL</th><th class="ms">Time</th></tr><tbody id="net"></tbody></table></div><div class="empty" id="netempty">No calls yet.</div></section>
<section id="log" hidden><div class="empty" id="logempty">No commands yet.</div></section></main></div>
<div id="mini" title="Switch device, or tap QA to reopen the runner"><span class="dot"></span>
<div class="minidevs"><button data-d="desktop" class="on" title="Desktop">Dsk</button><button data-d="iphone" title="iPhone">iOS</button><button data-d="android" title="Android">And</button><button data-d="tablet" title="Tablet">Tab</button></div>
<span class="label">QA</span></div>
<script>
const MINI_TOP=""" + json.dumps(MINI_CSS_TOP) + """;
const MINI_BOTTOM=""" + json.dumps(MINI_CSS_BOTTOM) + """;
const EXP_CSS=""" + json.dumps(EXPANDED_CSS) + """;
const ICON={pending:'○',running:'▶',verified:'✓',issue:'✗',cnv:'!',nt:'–'};
const S={cases:[],net:[],log:[]};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function tab(n){document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.tab===n));
  for(const id of ['tests','network','log'])document.getElementById(id).hidden=id!==n;}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>tab(b.dataset.tab));
function freeCorner(f){
  try{
    const w=window.top.innerWidth,h=window.top.innerHeight,doc=window.top.document;
    const prev=f.style.pointerEvents; f.style.pointerEvents='none';
    const topEl=doc.elementFromPoint(w-20,20), botEl=doc.elementFromPoint(w-20,h-20);
    f.style.pointerEvents=prev;
    const busy=el=>el&&el!==doc.body&&el!==doc.documentElement&&(el.closest('button,a,nav,header,[role="button"],[onclick]'));
    if(busy(topEl)&&!busy(botEl))return 'bottom';
    return 'top';
  }catch(e){return 'top';}
}
function toggle(mini){
  document.body.classList.toggle('mini',mini);
  const f=window.frameElement; if(!f)return;
  f.style.cssText=mini?(freeCorner(f)==='bottom'?MINI_BOTTOM:MINI_TOP):EXP_CSS;
}
document.getElementById('collapseBtn').onclick=()=>toggle(true);
document.getElementById('mini').onclick=()=>toggle(false);
document.getElementById('reportBtn').onclick=()=>{window.top.__qa_report_requested=true;};
function setDevice(name){
  document.querySelectorAll('[data-d]').forEach(b=>b.classList.toggle('on',b.dataset.d===name));
  window.top.__qa_pending_device=name;
}
document.querySelectorAll('[data-d]').forEach(b=>b.onclick=e=>{e.stopPropagation();setDevice(b.dataset.d);});
function counts(){const c={verified:0,issue:0,cnv:0,pending:0};for(const k of S.cases){if(k.status in c)c[k.status]++;else if(k.status!=='nt')c.pending++;}
  document.getElementById('counts').innerHTML=S.cases.length?`<span class="c-v"><b>${c.verified}</b> Verified</span><span class="c-i"><b>${c.issue}</b> Issue found</span><span class="c-n"><b>${c.cnv}</b> Could not verify</span><span class="c-p"><b>${c.pending}</b> to go</span>`:'';
  const m=document.getElementById('mini');m.classList.toggle('has-issue',c.issue>0);m.classList.toggle('has-pending',c.issue===0&&c.pending>0);m.classList.toggle('all-ok',c.issue===0&&c.pending===0&&S.cases.length>0);}
function render(){const el=document.getElementById('tests');
  if(!S.cases.length){el.innerHTML='<div class="empty">No test cases yet.</div>';counts();return;}
  el.innerHTML=S.cases.map(k=>`<div class="case ${k.status}"><div class="ct"><span class="ico">${k.status==='running'?'<span class="spin">'+ICON.running+'</span>':ICON[k.status]}</span><span class="id">${esc(k.id)}</span><span>${esc(k.title)}</span></div>
   <div class="steps">${k.steps.map(s=>`<div class="step ${s.status}"><span class="si">${s.status==='running'?'<span class="spin">'+ICON.running+'</span>':ICON[s.status]}</span><span>${esc(s.text)}</span>${s.ms!=null?`<span class="ms">${(s.ms/1000).toFixed(1)}s</span>`:''}</div>${s.msg&&s.status!=='pending'?`<div class="step ${s.status}"><div class="msg">${esc(s.msg)}</div></div>`:''}`).join('')}</div></div>`).join('');
  counts();const r=el.querySelector('.step.running')||el.querySelector('.case.running');if(r)r.scrollIntoView({block:'center'});}
function renderNet(){const tb=document.getElementById('net');document.getElementById('netempty').hidden=S.net.length>0;
  tb.innerHTML=S.net.slice().reverse().map(r=>{const cls=r.f||r.s>=400?'bad':r.s>=300?'mid':'ok';
   return `<tr><td class="m">${esc(r.m)}</td><td class="s ${cls}">${r.f?'ERR':esc(r.s??'...')}</td><td class="t">${esc(r.t)}</td><td title="${esc(r.u)}">${esc(r.u)}</td><td class="ms">${r.ms!=null?r.ms+' ms':''}</td></tr>`}).join('');}
function renderLog(){const el=document.getElementById('log');if(!S.log.length)return;
  el.innerHTML=S.log.slice().reverse().map(l=>`<div class="log step ${l.st}"><span class="si">${ICON[l.st]||''}</span><div><div>${esc(l.text)}</div>${l.msg?`<div class="msg" style="margin-left:0">${esc(l.msg)}</div>`:''}</div><span class="tm">${l.t}</span></div>`).join('');}
window.qa={
  plan(title,sub,cases){document.getElementById('title').textContent=title;document.getElementById('sub').textContent=sub||'';
    S.cases=cases.map(k=>({id:k.id,title:k.title,status:'pending',steps:k.steps.map(t=>({text:t,status:'pending',msg:'',ms:null}))}));render();tab('tests');},
  caseStatus(i,st){S.cases[i].status=st;render();},
  step(i,j,st,msg,ms){const s=S.cases[i].steps[j];s.status=st;s.msg=msg||'';s.ms=ms??null;render();},
  net(rows){S.net=S.net.concat(rows).slice(-400);renderNet();},
  log(st,text,msg){S.log.push({st,text,msg,t:new Date().toLocaleTimeString()});if(S.log.length>300)S.log.shift();renderLog();},
  done(text){document.getElementById('sub').textContent=text;},
  collapse(mini){toggle(!!mini);},
  markDevice(name){document.querySelectorAll('[data-d]').forEach(b=>b.classList.toggle('on',b.dataset.d===name));},
  restore(state){
    if(state.title!=null)document.getElementById('title').textContent=state.title;
    if(state.sub!=null)document.getElementById('sub').textContent=state.sub;
    if(state.cases)S.cases=state.cases;
    if(state.net)S.net=state.net;
    if(state.log)S.log=state.log;
    render();renderNet();renderLog();
  },
  tab
};
</script></body></html>"""


def inject(page):
    """Create the panel iframe if it is not already there. Cheap to call every time."""
    page.evaluate(CREATE_JS, [HTML, EXPANDED_CSS])


def ready(page):
    try:
        return bool(page.evaluate(READY_JS))
    except Exception:
        return False


class Panel:
    """Talks to the runner panel docked inside `page`. Every call is safe: a missing or broken panel
    never stops a test. Keeps its own copy of everything shown, so a page navigation (which wipes the
    iframe along with the rest of the DOM) loses nothing: the next call quietly reinjects and replays it."""

    def __init__(self, page):
        self.page = page
        self.broken = False
        self._title, self._sub = "QA Runner", ""
        self._cases, self._log, self._net = [], [], []

    @classmethod
    def open(cls, page):
        """Make sure the panel is showing right now (used by `start`/`panel`); check `.ok` for success."""
        p = cls(page)
        p._ensure()
        return p

    @classmethod
    def existing(cls, page):
        """A handle to the panel; it is created (or recreated) on first use, lazily."""
        return cls(page)

    def _ensure(self):
        if self.broken:
            return False
        try:
            if ready(self.page):
                return True
            inject(self.page)
            for _ in range(30):
                if ready(self.page):
                    if self._cases or self._log or self._net or self._sub:
                        self._replay()
                    return True
                self.page.wait_for_timeout(100)
            return False
        except Exception:
            self.broken = True
            return False

    def _replay(self):
        try:
            self.page.evaluate(CALL_JS, ["restore", [{"title": self._title, "sub": self._sub,
                                                       "cases": self._cases, "net": self._net, "log": self._log}]])
        except Exception:
            pass

    @property
    def ok(self):
        return self._ensure()

    def _call(self, name, *args):
        if not self._ensure():
            return
        try:
            self.page.evaluate(CALL_JS, [name, list(args)])
        except Exception:
            self.broken = True

    def plan(self, title, sub, cases):
        self._title, self._sub = title, sub
        self._cases = [{"id": k["id"], "title": k["title"], "status": "pending",
                        "steps": [{"text": t, "status": "pending", "msg": "", "ms": None} for t in k["steps"]]}
                       for k in cases]
        self._call("plan", title, sub, cases)

    def case(self, i, result):
        st = STATUS.get(result, result)
        if 0 <= i < len(self._cases):
            self._cases[i]["status"] = st
        self._call("caseStatus", i, st)

    def step(self, i, j, result, msg="", ms=None):
        st, msg = STATUS.get(result, result), core.redact(msg or "")
        if 0 <= i < len(self._cases) and 0 <= j < len(self._cases[i]["steps"]):
            s = self._cases[i]["steps"][j]
            s["status"], s["msg"], s["ms"] = st, msg, ms
        self._call("step", i, j, st, msg, ms)

    def net(self, rows):
        if rows:
            self._net = (self._net + rows)[-400:]
            self._call("net", rows)

    def log(self, result, text, msg=""):
        st, text, msg = STATUS.get(result, result), core.redact(text), core.redact(msg or "")
        self._log = (self._log + [{"st": st, "text": text, "msg": msg}])[-300:]
        self._call("log", st, text, msg)

    def tab(self, name):
        self._call("tab", name)

    def done(self, text):
        self._sub = text
        self._call("done", text)

    def collapse(self, mini=True):
        self._call("collapse", mini)

    def device(self, name):
        """Highlight the right button in the Desktop/iPhone/Android/Tablet row. Needed after a device
        switch that didn't originate from a click inside the panel (the `mobile` CLI command), since
        only a click updates that highlight on its own."""
        self._call("markDevice", name)

    def flash_network(self, page, ms=1100):
        """Open the Network tab for a moment so the user sees the calls, then go back to Tests."""
        if not self._ensure():
            return
        self.tab("network")
        page.wait_for_timeout(ms)
        self.tab("tests")
