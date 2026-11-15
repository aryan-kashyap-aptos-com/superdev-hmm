const $=s=>document.querySelector(s);
const state={files:[],cur:null,all:false};
const textCache=new Map();

function esc(s){return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function stats(t){const w=(t.match(/\S+/g)||[]).length;return{w,m:Math.max(1,Math.round(w/220))}}

async function fetchJSON(url,opts){const r=await fetch(url,opts);return r.json()}

async function loadList(){
  const files=await fetchJSON('/api/files');
  state.files=files;
  if(!state.cur&&files.length) state.cur=files[0].id;
  if(state.cur&&!files.find(f=>f.id===state.cur)) state.cur=files[0]?files[0].id:null;
  await Promise.all(files.filter(f=>!textCache.has(f.id)).map(async f=>{
    const d=await fetchJSON(`/api/files/${f.id}/raw`);
    textCache.set(f.id,d.text||'');
  }));
  render();
}

function renderFiles(){
  const ol=$('#files');$('#count').textContent=String(state.files.length).padStart(2,'0');
  if(!state.files.length){ol.innerHTML='<li class="empty">Nothing loaded. Add .md files or drop them anywhere on this window.</li>';return}
  ol.innerHTML='';
  state.files.forEach((f,i)=>{
    const li=document.createElement('li');li.className='file';li.draggable=true;li.dataset.id=f.id;
    li.tabIndex=0;li.setAttribute('aria-current',f.id===state.cur);
    const text=textCache.get(f.id)||'';
    const s=stats(text);
    li.innerHTML=`<span class="n">${String(i+1).padStart(2,'0')}</span><div class="nm"><b title="${esc(f.name)}">${esc(f.name)}</b><small>${s.w} words · ${s.m} min</small></div><button class="x" aria-label="Remove ${esc(f.name)}">×</button>`;
    li.addEventListener('click',e=>{if(e.target.closest('.x')){remove(f.id)}else open(f.id)});
    li.addEventListener('keydown',e=>{if(e.key==='Enter')open(f.id)});
    li.addEventListener('dragstart',e=>{li.classList.add('dragging');e.dataTransfer.setData('text/x-md',f.id);e.dataTransfer.effectAllowed='move'});
    li.addEventListener('dragend',()=>{li.classList.remove('dragging');clearDrop()});
    li.addEventListener('dragover',e=>{if(!e.dataTransfer.types.includes('text/x-md'))return;e.preventDefault();e.stopPropagation();clearDrop();const r=li.getBoundingClientRect();li.classList.add(e.clientY<r.top+r.height/2?'drop-t':'drop-b')});
    li.addEventListener('drop',async e=>{const id=e.dataTransfer.getData('text/x-md');if(!id)return;e.preventDefault();e.stopPropagation();
      const before=li.classList.contains('drop-t');clearDrop();
      const ids=state.files.map(x=>x.id);
      const from=ids.indexOf(id);const [m]=ids.splice(from,1);
      let to=ids.indexOf(f.id);if(!before)to++;ids.splice(to,0,m);
      state.files=await fetchJSON('/api/files/order',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({order:ids})});
      render();
    });
    ol.appendChild(li);
  });
}
function clearDrop(){document.querySelectorAll('.drop-t,.drop-b').forEach(e=>e.classList.remove('drop-t','drop-b'))}
async function remove(id){
  state.files=await fetchJSON(`/api/files/${id}`,{method:'DELETE'});
  textCache.delete(id);
  if(state.cur===id){const i=0;state.cur=state.files[i]?state.files[i].id:null}
  render();
}
function open(id){
  state.cur=id;
  if(state.all){
    renderFiles();
    const target=document.getElementById('sec-'+id);
    if(target) target.scrollIntoView({behavior:'smooth',block:'start'});
    return;
  }
  render();
}
/* outline/tree code blocks (plain-fenced file trees, layout diagrams) rendered as aligned rows instead of a scrolling wall of monospace */
function looksLikeOutline(code){
  const lines=code.split('\n').filter(l=>l.trim());
  if(lines.length<2)return false;
  const withTreeChars=lines.filter(l=>/^[\s│├└─]*[├└]/.test(l)).length;
  return withTreeChars/lines.length>=0.5;
}
function renderOutlineHtml(code){
  const rows=code.split('\n').map(line=>{
    if(!line.trim())return '<div class="tree-row tree-blank">&nbsp;</div>';
    const m=line.match(/^([\s│├└─]*)([\s\S]*)$/);
    const prefix=m?m[1]:'';
    const rest=m?m[2]:line;
    const parts=rest.split(/ {2,}/).map(s=>s.trim()).filter(Boolean);
    const name=parts.shift()||'';
    const isDir=/\/\s*$/.test(name);
    const descs=parts.map((p,i)=>`<span class="tree-desc${i===parts.length-1&&parts.length>1?' tree-tag':''}">${esc(p)}</span>`).join('');
    return `<div class="tree-row"><span class="tree-prefix">${esc(prefix)}</span><span class="tree-name${isDir?' tree-dir':''}">${esc(name)}</span>${descs}</div>`;
  }).join('');
  return `<pre class="tree-block" data-raw="${encodeURIComponent(code)}"><div class="tree-body">${rows}</div></pre>`;
}
const treeRenderer=new marked.Renderer();
const _defaultCode=treeRenderer.code.bind(treeRenderer);
treeRenderer.code=(...args)=>{
  const [code,infostring]=args;
  if(!infostring&&looksLikeOutline(code))return renderOutlineHtml(code);
  return _defaultCode(...args);
};
function renderHtml(md){return marked.parse(md,{gfm:true,breaks:false,renderer:treeRenderer})}
try{mermaid.initialize({startOnLoad:false,theme:'dark',securityLevel:'loose',fontFamily:'JetBrains Mono, monospace'})}catch(e){}
let mermaidSeq=0;
async function renderMermaid(art){
  const blocks=[...art.querySelectorAll('pre code.language-mermaid')];
  for(const code of blocks){
    const pre=code.parentElement;
    const src=code.textContent;
    const id='mmd-'+(++mermaidSeq);
    try{
      const {svg}=await mermaid.render(id,src);
      const div=document.createElement('div');div.className='mermaid-diagram';div.innerHTML=svg;
      pre.replaceWith(div);
    }catch(e){
      pre.insertAdjacentHTML('beforebegin',`<p class="hint" style="color:var(--accent)">Diagram failed to render: ${esc(e.message||'parse error')}</p>`);
    }
  }
}
function attachCodeExtras(art){
  [...art.querySelectorAll('pre')].filter(pre=>!pre.querySelector('code.language-mermaid')).forEach(pre=>{const b=document.createElement('button');b.className='copy';b.textContent='Copy';
    b.onclick=async()=>{const text=pre.dataset.raw?decodeURIComponent(pre.dataset.raw):pre.innerText.replace(/Copy$/,'').trimEnd();try{await navigator.clipboard.writeText(text);b.textContent='Copied'}catch(e){b.textContent='Select + Ctrl+C'}setTimeout(()=>b.textContent='Copy',1400)};pre.appendChild(b)});
  renderMermaid(art);
  art.querySelectorAll('img').forEach(img=>{
    const src=img.getAttribute('src')||'';
    const original=img.getAttribute('alt')||src;
    if(/^(https?:)?\/\//.test(src)||src.startsWith('data:')){
      img.onerror=()=>showMissingImage(img,original,false);
      return;
    }
    const base=src.split('/').pop().split('?')[0];
    img.setAttribute('src','/api/assets/'+encodeURIComponent(base));
    img.onerror=()=>showMissingImage(img,base,true);
  });
}
function showMissingImage(img,name,local){
  if(img.dataset.placeholderShown)return;
  img.dataset.placeholderShown='1';
  const div=document.createElement('div');
  div.className='img-missing';
  div.innerHTML=local
    ? `<b>Image not added:</b> <span class="mono">${esc(name)}</span><br>Drag or select this file alongside the .md to show it here.`
    : `<b>Image failed to load:</b> <span class="mono">${esc(name)}</span>`;
  img.replaceWith(div);
}
function wireToc(toc){
  toc.querySelectorAll('a').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();document.getElementById(a.getAttribute('href').slice(1)).scrollIntoView({behavior:'smooth',block:'start'})}));
}
function renderAllView(art,toc){
  $('#fname').textContent=`All ${state.files.length} files, in order`;
  const totalWords=state.files.reduce((a,f)=>a+stats(textCache.get(f.id)||'').w,0);
  $('#fmeta').textContent=`${state.files.length} FILES COMBINED  ·  ${totalWords} WORDS  ·  ${Math.max(1,Math.round(totalWords/220))} MIN READ`;
  art.className='enter';
  art.innerHTML='<div class="prose">'+state.files.map(f=>
    `<section class="doc-section" id="sec-${f.id}"><p class="doc-divider">${esc(f.name)}</p>${renderHtml(textCache.get(f.id)||'')}</section>`
  ).join('')+'</div>';
  attachCodeExtras(art);
  let tocHtml='';
  state.files.forEach(f=>{
    const sec=document.getElementById('sec-'+f.id);
    const hs=[...sec.querySelectorAll('h2,h3')];
    hs.forEach((h,i)=>h.id=`h-${f.id}-${i}`);
    if(hs.length) tocHtml+=`<h6>${esc(f.name)}</h6>`+hs.map(h=>`<a href="#${h.id}" class="${h.tagName==='H3'?'l3':''}">${esc(h.textContent)}</a>`).join('');
  });
  toc.innerHTML=tocHtml;
  wireToc(toc);
  $('#scroll').scrollTop=0;onScroll();
}
function render(){
  renderFiles();
  const art=$('#article'),toc=$('#toc');
  const dis=!state.files.length;$('#expWord').disabled=dis;$('#expPdf').disabled=dis;
  if(!state.files.length){$('#fname').textContent='No file';$('#fmeta').textContent='';
    art.innerHTML='<div class="welcome" style="height:60vh"><div>Add a markdown file to begin.<span>press O or drop files anywhere</span></div></div>';toc.innerHTML='';return}
  if(state.all){renderAllView(art,toc);return}
  const f=state.files.find(x=>x.id===state.cur);
  if(!f){$('#fname').textContent='No file';$('#fmeta').textContent='';
    art.innerHTML='<div class="welcome" style="height:60vh"><div>Add a markdown file to begin.<span>press O or drop files anywhere</span></div></div>';toc.innerHTML='';return}
  $('#fname').textContent=f.name;const text=textCache.get(f.id)||'';const s=stats(text);
  $('#fmeta').textContent=`${String(state.files.indexOf(f)+1).padStart(2,'0')} / ${String(state.files.length).padStart(2,'0')}  ·  ${s.w} WORDS  ·  ${s.m} MIN READ`;
  art.className='enter';art.innerHTML='<div class="prose">'+renderHtml(text)+'</div>';
  attachCodeExtras(art);
  const hs=[...art.querySelectorAll('h2,h3')];
  hs.forEach((h,i)=>h.id='h'+i);
  toc.innerHTML=hs.length?'<h6>On this page</h6>'+hs.map((h,i)=>`<a href="#h${i}" class="${h.tagName==='H3'?'l3':''}">${esc(h.textContent)}</a>`).join(''):'';
  wireToc(toc);
  $('#scroll').scrollTop=0;onScroll();
}
function onScroll(){
  const sc=$('#scroll');const p=sc.scrollHeight-sc.clientHeight;
  $('#progress').style.width=(p>0?sc.scrollTop/p*100:0)+'%';
  const hs=[...document.querySelectorAll('#article h2,#article h3')];let on=null;
  hs.forEach(h=>{if(h.getBoundingClientRect().top<160)on=h.id});
  document.querySelectorAll('#toc a').forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+on));
}
$('#scroll').addEventListener('scroll',onScroll,{passive:true});

/* loading */
async function ingest(list){
  const all=[...list];
  const mdFiles=all.filter(f=>/\.(md|markdown|txt)$/i.test(f.name));
  const imgFiles=all.filter(f=>/^image\//.test(f.type)||/\.(png|jpe?g|gif|webp|svg)$/i.test(f.name));
  if(!mdFiles.length&&!imgFiles.length){toast('Only .md, .markdown, .txt or image files');return}
  if(imgFiles.length){
    const form=new FormData();
    for(const f of imgFiles) form.append('files',f);
    await fetchJSON('/api/assets',{method:'POST',body:form});
  }
  if(mdFiles.length){
    const form=new FormData();
    for(const f of mdFiles) form.append('files',f);
    const data=await fetchJSON('/api/files',{method:'POST',body:form});
    state.cur=data.added.length?data.added[data.added.length-1].id:state.cur;
  }
  await loadList();
  const parts=[];
  if(mdFiles.length) parts.push(`${mdFiles.length} file${mdFiles.length>1?'s':''}`);
  if(imgFiles.length) parts.push(`${imgFiles.length} image${imgFiles.length>1?'s':''}`);
  toast(`Added ${parts.join(' + ')}`);
}
$('#addBtn').onclick=()=>$('#picker').click();
$('#picker').onchange=e=>{ingest(e.target.files);e.target.value=''};
let dc=0;
addEventListener('dragenter',e=>{if(e.dataTransfer.types.includes('Files')){dc++;document.body.classList.add('dragover')}});
addEventListener('dragleave',e=>{if(e.dataTransfer.types.includes('Files')){dc=Math.max(0,dc-1);if(!dc)document.body.classList.remove('dragover')}});
addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('Files'))e.preventDefault()});
addEventListener('drop',e=>{if(e.dataTransfer.files.length){e.preventDefault();dc=0;document.body.classList.remove('dragover');ingest(e.dataTransfer.files)}});
addEventListener('keydown',e=>{
  if(e.target.matches('input,textarea')||e.metaKey||e.ctrlKey)return;
  const i=state.files.findIndex(f=>f.id===state.cur);
  if(e.key==='o')$('#picker').click();
  if(e.key==='f')$('#focusBtn').click();
  if(e.key==='t')$('#themeBtn').click();
  if(e.key==='j'&&state.files[i+1])open(state.files[i+1].id);
  if(e.key==='k'&&state.files[i-1])open(state.files[i-1].id);
});

/* export (server-side: real PDF + Word via Playwright/python-docx) */
function setScope(all){state.all=all;$('#scopeAll').setAttribute('aria-pressed',all);$('#scopeOne').setAttribute('aria-pressed',!all);render()}
$('#scopeOne').onclick=()=>setScope(false);$('#scopeAll').onclick=()=>setScope(true);
function scopeIds(){return state.all?null:(state.cur?[state.cur]:null)}
async function exportAs(kind){
  const ids=scopeIds();
  if(!state.all&&!state.cur)return;
  toast(`Building ${kind.toUpperCase()}…`);
  const res=await fetch(`/api/export/${kind}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids})});
  if(!res.ok){toast('Export failed');return}
  const blob=await res.blob();
  const f=state.files.find(x=>x.id===state.cur);
  const name=state.all?`notes.${kind}`:`${(f?f.name:'notes').replace(/\.\w+$/,'')}.${kind}`;
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(a.href),2000);
  toast(`${kind.toUpperCase()} saved`);
}
$('#expWord').onclick=()=>exportAs('docx');
$('#expPdf').onclick=()=>exportAs('pdf');

let tt;function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');clearTimeout(tt);tt=setTimeout(()=>t.classList.remove('show'),2200)}

let fs=1;
function applyFontScale(){
  document.documentElement.style.setProperty('--fs',fs);
  $('#fsPct').textContent=Math.round(fs*100)+'%';
  try{localStorage.setItem('md_reader_fontscale',fs)}catch(e){}
}
$('#fsUp').onclick=()=>{fs=Math.min(1.7,+(fs+.1).toFixed(2));applyFontScale()};
$('#fsDown').onclick=()=>{fs=Math.max(.65,+(fs-.1).toFixed(2));applyFontScale()};
$('#themeBtn').onclick=()=>{const l=document.body.classList.toggle('light');$('#themeBtn').setAttribute('aria-pressed',l);try{localStorage.setItem('md_reader_theme',l?'light':'dark')}catch(e){}};
$('#focusBtn').onclick=()=>{const f=document.body.classList.toggle('focus');$('#focusBtn').setAttribute('aria-pressed',f)};
function setReadFont(v){
  document.body.classList.toggle('sans-font',v==='sans');
  $('#fontSerifBtn').setAttribute('aria-pressed',String(v!=='sans'));
  $('#fontSansBtn').setAttribute('aria-pressed',String(v==='sans'));
  try{localStorage.setItem('md_reader_font',v)}catch(e){}
}
$('#fontSerifBtn').onclick=()=>setReadFont('serif');
$('#fontSansBtn').onclick=()=>setReadFont('sans');

try{if(localStorage.getItem('md_reader_theme')==='light'){document.body.classList.add('light');$('#themeBtn').setAttribute('aria-pressed','true')}}catch(e){}
try{setReadFont(localStorage.getItem('md_reader_font')||'serif')}catch(e){}
try{const saved=parseFloat(localStorage.getItem('md_reader_fontscale'));if(saved)fs=saved}catch(e){}
applyFontScale();
loadList();
