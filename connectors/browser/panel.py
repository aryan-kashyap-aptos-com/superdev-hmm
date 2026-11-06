"""The runner panel: a Cypress-style sidebar in its own window, docked on the left of the screen.

It shows the test cases and their steps before they run (grey), the one running now (blue),
and each result as it happens (green Verified, red Issue found, amber Could not verify, grey Not tested).
Tabs: Tests, Network (the calls each step made, flashed open after a step that loaded something), and Log
(single commands run by hand). It is only a viewer: if it is closed or breaks, the tests carry on.

It lives in a separate window, not inside the page under test, so it never changes that page,
its layout, its element checks, or its screenshots.
"""
import core

URL = "about:blank" + core.PANEL_MARK
WIDTH = 420
STATUS = {"Verified": "verified", "Issue found": "issue", "Could not verify": "cnv", "Not tested": "nt"}

HTML = r"""<!doctype html><html><head><meta charset="utf-8"><title>QA Runner</title><style>
:root{--bg:#171a26;--top:#1f2233;--line:#2c3047;--text:#d6d9e6;--dim:#7c829b;--green:#3fb950;--red:#f85149;--amber:#d9a521;--blue:#58a6ff}
*{box-sizing:border-box}body{margin:0;font:13px/1.45 "Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--text)}
header{position:sticky;top:0;z-index:2;background:var(--top);border-bottom:1px solid var(--line)}
.head{padding:10px 12px 6px}h1{font-size:14px;margin:0;font-weight:600}.sub{color:var(--dim);font-size:12px;margin-top:2px}
.counts{display:flex;gap:12px;margin-top:6px;font-size:12px}.counts b{font-weight:600}
.c-v{color:var(--green)}.c-i{color:var(--red)}.c-n{color:var(--amber)}.c-p{color:var(--dim)}
nav{display:flex;padding:0 6px}nav button{background:none;border:0;border-bottom:2px solid transparent;color:var(--dim);padding:7px 10px;font:inherit;cursor:pointer}
nav button.on{color:var(--text);border-color:var(--blue)}
.case{border-bottom:1px solid var(--line)}.ct{display:flex;gap:8px;padding:8px 12px;align-items:flex-start;font-weight:600}
.case.running>.ct{background:#22304d}.id{color:var(--dim);font-weight:400;flex:none}
.ico{width:16px;flex:none;text-align:center;font-weight:700}
.pending>.ct .ico,.pending .si{color:var(--dim)}.running>.ct .ico,.step.running .si{color:var(--blue)}
.verified>.ct .ico,.step.verified .si{color:var(--green)}.issue>.ct .ico,.step.issue .si{color:var(--red)}
.cnv>.ct .ico,.step.cnv .si{color:var(--amber)}.nt>.ct .ico,.step.nt .si{color:var(--dim)}
.steps{padding:0 12px 8px 36px}.step{display:flex;gap:8px;padding:2px 0;color:var(--dim)}
.step.running{color:var(--text);font-weight:600}.step.verified,.step.issue,.step.cnv{color:var(--text)}
.si{width:14px;flex:none;text-align:center}.ms{margin-left:auto;color:var(--dim);font-size:11px;flex:none;padding-left:6px}
.msg{font-size:12px;margin:1px 0 4px 22px;white-space:pre-wrap;word-break:break-word}.issue .msg{color:#ff9b95}.cnv .msg{color:#f0c96a}.verified .msg{color:var(--dim)}
.spin{display:inline-block;animation:p 1s infinite}@keyframes p{50%{opacity:.25}}
table{width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed}td{padding:3px 6px;border-bottom:1px solid var(--line);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
td.m{width:46px;color:var(--dim)}td.s{width:38px}td.t{width:62px;color:var(--dim)}td.ms{width:56px;text-align:right;color:var(--dim)}
.ok{color:var(--green)}.bad{color:var(--red)}.mid{color:var(--amber)}
.log{padding:6px 12px;border-bottom:1px solid var(--line);display:flex;gap:8px}.log .tm{color:var(--dim);font-size:11px;flex:none}
.empty{color:var(--dim);padding:14px 12px}
</style></head><body>
<header><div class="head"><h1 id="title">QA Runner</h1><div class="sub" id="sub">Waiting for a scenario. Single commands appear under Log.</div>
<div class="counts" id="counts"></div></div>
<nav><button data-tab="tests" class="on">Tests</button><button data-tab="network">Network</button><button data-tab="log">Log</button></nav></header>
<main><section id="tests"><div class="empty">No test cases yet.</div></section>
<section id="network" hidden><table><tbody id="net"></tbody></table><div class="empty" id="netempty">No calls yet.</div></section>
<section id="log" hidden><div class="empty" id="logempty">No commands yet.</div></section></main>
<script>
const ICON={pending:'○',running:'▶',verified:'✓',issue:'✗',cnv:'!',nt:'–'};
const S={cases:[],net:[],log:[]};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function tab(n){document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.tab===n));
  for(const id of ['tests','network','log'])document.getElementById(id).hidden=id!==n;}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>tab(b.dataset.tab));
function counts(){const c={verified:0,issue:0,cnv:0,pending:0};for(const k of S.cases){if(k.status in c)c[k.status]++;else if(k.status!=='nt')c.pending++;}
  document.getElementById('counts').innerHTML=S.cases.length?`<span class="c-v"><b>${c.verified}</b> Verified</span><span class="c-i"><b>${c.issue}</b> Issue found</span><span class="c-n"><b>${c.cnv}</b> Could not verify</span><span class="c-p"><b>${c.pending}</b> to go</span>`:'';}
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
  tab
};
</script></body></html>"""


def find(context):
    return next((pg for pg in context.pages if core.is_panel(pg)), None)


def _window_id(cdp, page):
    target = page.context.new_cdp_session(page).send("Target.getTargetInfo")["targetInfo"]["targetId"]
    return cdp.send("Browser.getWindowForTarget", {"targetId": target})["windowId"]


def arrange(browser, app, pg):
    """Panel on the left edge of the screen, the site to its right, both full height."""
    try:
        cdp = browser.new_browser_cdp_session()
        left, top, width, height = app.evaluate("() => [screen.availLeft || 0, screen.availTop || 0, screen.availWidth, screen.availHeight]")
        for page, bounds in ((pg, {"left": left, "top": top, "width": WIDTH, "height": height}),
                             (app, {"left": left + WIDTH, "top": top, "width": max(900, width - WIDTH), "height": height})):
            wid = _window_id(cdp, page)
            cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {"windowState": "normal"}})
            cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": bounds})
    except Exception:
        pass   # placement is a nicety; the panel works wherever it is


def ensure(browser, app):
    """Open the panel window (or reuse it) and return its page."""
    pg = find(app.context)
    if pg is None:
        browser.new_browser_cdp_session().send("Target.createTarget", {"url": URL, "newWindow": True})
        for _ in range(50):
            app.wait_for_timeout(100)
            pg = find(app.context)
            if pg:
                break
        if pg is None:
            return None
        pg.set_content(HTML)
        arrange(browser, app, pg)
        app.bring_to_front()
    elif not pg.evaluate("() => !!window.qa"):
        pg.set_content(HTML)
    return pg


class Panel:
    """Talks to the panel window. Every call is safe: a closed or broken panel never stops a test."""

    def __init__(self, pg):
        self.pg = pg

    @classmethod
    def open(cls, browser, app):
        try:
            return cls(ensure(browser, app))
        except Exception:
            return cls(None)

    @classmethod
    def existing(cls, app):
        pg = find(app.context)
        try:
            return cls(pg if pg and pg.evaluate("() => !!window.qa") else None)
        except Exception:
            return cls(None)

    def _call(self, name, *args):
        if self.pg is None:
            return
        try:
            self.pg.evaluate("([n, a]) => window.qa && window.qa[n](...a)", [name, list(args)])
        except Exception:
            self.pg = None

    def plan(self, title, sub, cases):
        self._call("plan", title, sub, cases)

    def case(self, i, result):
        self._call("caseStatus", i, STATUS.get(result, result))

    def step(self, i, j, result, msg="", ms=None):
        self._call("step", i, j, STATUS.get(result, result), core.redact(msg or ""), ms)

    def net(self, rows):
        if rows:
            self._call("net", rows)

    def log(self, result, text, msg=""):
        self._call("log", STATUS.get(result, result), core.redact(text), core.redact(msg or ""))

    def tab(self, name):
        self._call("tab", name)

    def done(self, text):
        self._call("done", text)

    def flash_network(self, page, ms=1100):
        """Open the Network tab for a moment so the user sees the calls, then go back to Tests."""
        if self.pg is None:
            return
        self.tab("network")
        page.wait_for_timeout(ms)
        self.tab("tests")
