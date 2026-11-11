P = "/home/hatch/workspace/devryx-ai/public/index.html"
s = open(P, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    assert s.count(old) == 1, "ANCHOR (count=%d): %s" % (s.count(old), old[:80])
    s = s.replace(old, new, count)

# 1) Video CSS before </style>
rep("</style>",
"""/* ═══════════ VIDEO GENERATION ═══════════ */
#vidbtn{
  width:36px;height:36px;border-radius:9px;flex-shrink:0;
  background:var(--s3);border:1px solid var(--border2);color:var(--text2);
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:all .15s;
}
#vidbtn:hover{border-color:var(--red);color:var(--red)}
#vidbtn.on{background:linear-gradient(135deg,var(--red),var(--red2));border-color:var(--red);color:#fff;box-shadow:0 0 10px rgba(var(--red-rgb),0.5)}
#vidbtn svg{width:15px;height:15px}
.vid-progress{display:flex;flex-direction:column;align-items:center;gap:10px;padding:20px 12px;min-width:230px;text-align:center}
.vid-spin{width:34px;height:34px;border-radius:50%;border:3px solid var(--border2);border-top-color:var(--red);animation:vidspin 0.9s linear infinite}
@keyframes vidspin{to{transform:rotate(360deg)}}
.vid-status{font-size:13px;font-weight:600}
.vid-hint{font-size:11.5px;color:var(--text2)}
.vid-cancel{background:none;border:1px solid var(--border2);color:var(--text2);border-radius:999px;padding:5px 16px;font-size:12px;font-family:var(--font);cursor:pointer}
.vid-cancel:hover{border-color:var(--red);color:var(--red)}
video.gen-vid{width:100%;max-width:430px;border-radius:12px;display:block;background:#000}
</style>""")

# 2) Video button in composer, before send button
rep('<button id="sendbtn" onclick="send()" aria-label="Send">',
"""<button id="vidbtn" onclick="toggleVideoMode()" title="Generate a video instead of text">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M7 4v16M17 4v16M2 9h5M2 15h5M17 9h5M17 15h5"/></svg>
            </button>
            <button id="sendbtn" onclick="send()" aria-label="Send">""")

# 3) Video JS before textOf()
rep("function textOf(content){",
"""/* ── VIDEO GENERATION (free Zeroscope model via public HF Space) ── */
const VIDEO_API = 'https://hysts-zeroscope-v2.hf.space';
let videoMode = false;
const vidBtn = document.getElementById('vidbtn');
function toggleVideoMode(){
  if(imageMode) toggleImageMode();
  videoMode = !videoMode;
  vidBtn.classList.toggle('on', videoMode);
  if(videoMode && pendingAttachment) clearAttachment();
  inputEl.placeholder = videoMode
    ? 'Describe the video you want... (e.g. "ocean waves at sunset")'
    : 'Ask anything... (Enter to send · Shift+Enter for new line)';
  hintEl.innerHTML = videoMode
    ? 'Video mode is ON \\u2014 describe a scene and I\\u2019ll generate a short clip &nbsp;·&nbsp; Click the film icon again to go back to chat'
    : 'Enter to send &nbsp;·&nbsp; Shift+Enter for new line';
}
function detectVideoIntent(text){
  const t = text.toLowerCase().trim();
  const patterns = [
    /^(make|create|generate|render)\\b.*\\bvideo\\b/,
    /\\bvideo\\s+of\\b/,
    /^(can you |please )?(animate|film)\\b/
  ];
  return patterns.some(p => p.test(t));
}
function addVideoMsg(url){
  removeWelcome();
  const wrap = document.createElement('div');
  wrap.className = 'msg ai';
  wrap.innerHTML = `<div class="av ai-av">${AI_SVG}</div><div class="mc"><div class="mname">AI Assistant</div><div class="bubble-wrap"><div class="bubble"><video class="gen-vid" controls playsinline preload="metadata" src="${esc(url)}"></video></div><div class="msg-actions"></div></div></div></div>`;
  const dlBtn = document.createElement('button');
  dlBtn.className = 'act-btn';
  dlBtn.innerHTML = COPY_SVG + ' Download';
  dlBtn.onclick = async () => {
    dlBtn.innerHTML = 'Saving...';
    try{
      const r = await fetch(url);
      const blob = await r.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `video-${Date.now()}.mp4`;
      a.click();
      setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
    }catch(e){ window.open(url, '_blank'); }
    dlBtn.innerHTML = COPY_SVG + ' Download';
  };
  wrap.querySelector('.msg-actions').appendChild(dlBtn);
  msgsEl.appendChild(wrap);
  const nearBottom = msgsEl.scrollHeight - msgsEl.scrollTop - msgsEl.clientHeight < 200;
  if(nearBottom) scrollToBottom();
  return wrap;
}
function addVideoProgress(ctrl){
  removeWelcome();
  const wrap = document.createElement('div');
  wrap.className = 'msg ai';
  wrap.innerHTML = `<div class="av ai-av">${AI_SVG}</div><div class="mc"><div class="mname">AI Assistant</div><div class="bubble-wrap"><div class="bubble"><div class="vid-progress"><div class="vid-spin"></div><div class="vid-status">Starting video generation...</div><div class="vid-hint">Running on a free GPU \\u00b7 usually takes 1\\u20134 minutes</div><button class="vid-cancel">Cancel</button></div></div></div></div></div>`;
  msgsEl.appendChild(wrap);
  scrollToBottom();
  const statusEl = wrap.querySelector('.vid-status');
  wrap.querySelector('.vid-cancel').onclick = ()=>{ ctrl.cancelled = true; };
  return {
    wrap,
    setStatus(t){ if(statusEl) statusEl.textContent = t; }
  };
}
function handleVideoEvent(evt, setStatus){
  if(!evt || !evt.msg) return;
  if(evt.msg === 'estimation'){
    const rank = (evt.rank != null) ? ` #${evt.rank}` : '';
    setStatus(`In queue${rank}... waiting for a free GPU`);
  }else if(evt.msg === 'process_starts'){
    setStatus('Warming up the video model...');
  }else if(evt.msg === 'progress' && Array.isArray(evt.progress_data) && evt.progress_data[0]){
    const p = evt.progress_data[0];
    if(typeof p.index === 'number' && typeof p.length === 'number' && p.length > 0){
      setStatus(`Rendering frames... ${Math.round((p.index/p.length)*100)}%`);
    }else{
      setStatus('Rendering frames...');
    }
  }else if(evt.msg === 'process_generating'){
    setStatus('Generating video...');
  }
}
async function streamVideoEvents(eventId, setStatus, ctrl){
  const res = await fetch(`${VIDEO_API}/gradio_api/call/run/${eventId}`, {headers:{'Accept':'text/event-stream'}});
  if(!res.ok || !res.body) throw new Error('Could not connect to the video service.');
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  const started = Date.now();
  const TIMEOUT_MS = 8*60*1000;
  try{
    while(true){
      if(ctrl.cancelled) throw new Error('cancelled');
      if(Date.now()-started > TIMEOUT_MS) throw new Error('Video is taking too long (over 8 minutes). The free GPU is likely busy \\u2014 try again later.');
      const {done, value} = await reader.read();
      if(done) break;
      buf += dec.decode(value, {stream:true});
      let idx;
      while((idx = buf.indexOf('\\n\\n')) >= 0){
        const chunk = buf.slice(0, idx);
        buf = buf.slice(idx+2);
        for(const line of chunk.split('\\n')){
          if(!line.startsWith('data: ')) continue;
          let evt;
          try{ evt = JSON.parse(line.slice(6)); }catch(e){ continue; }
          handleVideoEvent(evt, setStatus);
          if(evt.msg === 'complete'){
            if(evt.success === false){
              const em = (evt.output && evt.output.error) ? String(evt.output.error).slice(0,160) : 'Video generation failed on the server.';
              throw new Error(em);
            }
            const file = evt.output && evt.output.data && evt.output.data[0];
            let url = file && (file.url || file.path);
            if(!url) throw new Error('Video service returned no file.');
            if(url.startsWith('/')) url = VIDEO_API + url;
            return url;
          }
        }
      }
    }
  }finally{
    try{ reader.cancel(); }catch(e){}
  }
  throw new Error('Video stream ended unexpectedly. Try again.');
}
async function handleVideoGen(prompt){
  addMsg('user', prompt);
  history.push({role:'user', content:`[Video request] ${prompt}`});
  persistCurrent();
  const ctrl = {cancelled:false};
  const prog = addVideoProgress(ctrl);
  try{
    setStatusSafe(prog, 'Contacting video service...');
    const r = await fetch(`${VIDEO_API}/gradio_api/call/run`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({data:[prompt, 0, 24, 25]})
    });
    const j = await r.json().catch(()=>({}));
    if(!j || !j.event_id) throw new Error('Video service is busy right now. Try again in a bit.');
    const url = await streamVideoEvents(j.event_id, prog.setStatus, ctrl);
    prog.wrap.remove();
    addVideoMsg(url);
    history.push({role:'assistant', content:`[Video] ${url}`});
    persistCurrent();
  }catch(err){
    if(ctrl.cancelled || /cancelled/i.test(err && err.message || '')){
      prog.wrap.remove();
    }else{
      prog.setStatus('Failed: ' + (err.message || 'Video generation failed.'));
      const hint = prog.wrap.querySelector('.vid-hint');
      if(hint) hint.textContent = 'You can try again with a simpler prompt.';
      const cancelBtn = prog.wrap.querySelector('.vid-cancel');
      if(cancelBtn) cancelBtn.remove();
    }
  }
  sendBtn.disabled = false;
  inputEl.focus();
}
function setStatusSafe(prog, t){ try{ prog.setStatus(t); }catch(e){} }

function textOf(content){""")

# 4) send(): compute useVideoGen
rep("const locIntent = !attachment && !imageMode && !useImageGen && detectLocationIntent(text);",
"""const locIntent = !attachment && !imageMode && !useImageGen && detectLocationIntent(text);
  const useVideoGen = !attachment && !imageMode && (videoMode || detectVideoIntent(text));""")

# 5) send(): video branch after the location branch
rep("""  if(locIntent){
    handleLocationIntent(locIntent, text);
    return;
  }""",
"""  if(locIntent){
    handleLocationIntent(locIntent, text);
    return;
  }

  if(useVideoGen){
    handleVideoGen(text);
    return;
  }""")

# 6) loadSession: render saved videos as players
rep("history.forEach(m=> addMsg(m.role==='assistant'?'ai':'user', textOf(m.content), false, null, imageOf(m.content)));",
"""history.forEach(m=>{
    const t = textOf(m.content);
    const vm = m.role==='assistant' && /^\\[Video\\] (\\S+)/.exec(t);
    if(vm) addVideoMsg(vm[1]);
    else addMsg(m.role==='assistant'?'ai':'user', t, false, null, imageOf(m.content));
  });""")

# 7) regenerate guard: skip video entries too
rep("/^\\[(Map|Image request)\\]/", "/^\\[(Map|Image request|Video request|Video)\\]/")

# 8) toggleImageMode: video mode is mutually exclusive too
rep("""function toggleImageMode(){
  imageMode = !imageMode;""",
"""function toggleImageMode(){
  if(videoMode) toggleVideoMode();
  imageMode = !imageMode;""")

# 9) New welcome chip
rep('<button class="chip" onclick="ask(this)">Weather in Tokyo</button>',
"""<button class="chip" onclick="ask(this)">Weather in Tokyo</button>
            <button class="chip" onclick="ask(this)">Generate a video of ocean waves</button>""")

# 10) Welcome paragraph mentions videos
rep("image understanding, file generation, maps &amp; weather, or just thinking through a problem together, in any language.",
    "image understanding, file generation, maps &amp; weather, short videos, or just thinking through a problem together, in any language.")

open(P, "w", encoding="utf-8").write(s)
print("video UI applied OK")
