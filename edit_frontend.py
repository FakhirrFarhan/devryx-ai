import re, sys

P = "/home/hatch/workspace/devryx-ai/public/index.html"
s = open(P, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    assert s.count(old) >= 1, "ANCHOR NOT FOUND: " + old[:80]
    s = s.replace(old, new, count)

# 1) Leaflet CDN in <head>
rep("</head>",
"""<!-- Leaflet maps (free, no key) -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>""")

# 2) Aurora theme + map styles before </style>
rep("</style>",
"""/* ═══════════ DEVRYX AURORA THEME + MAPS ═══════════ */
body::before{
  content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background:
    radial-gradient(640px 420px at 12% 8%, rgba(230,57,70,0.10), transparent 60%),
    radial-gradient(720px 520px at 88% 18%, rgba(124,58,237,0.12), transparent 60%),
    radial-gradient(860px 620px at 50% 108%, rgba(37,99,235,0.10), transparent 60%);
  animation:aurora 26s ease-in-out infinite alternate;
}
@keyframes aurora{
  0%{transform:translate3d(0,0,0) scale(1)}
  50%{transform:translate3d(2%,3%,0) scale(1.06)}
  100%{transform:translate3d(-2%,-2%,0) scale(1.03)}
}
body.light::before{
  background:
    radial-gradient(640px 420px at 12% 8%, rgba(230,57,70,0.07), transparent 60%),
    radial-gradient(720px 520px at 88% 18%, rgba(124,58,237,0.08), transparent 60%),
    radial-gradient(860px 620px at 50% 108%, rgba(37,99,235,0.07), transparent 60%);
}
#shell{position:relative;z-index:1}
#inputwrap{
  background:rgba(24,24,28,0.72);
  -webkit-backdrop-filter:blur(18px) saturate(1.35);
  backdrop-filter:blur(18px) saturate(1.35);
  box-shadow:0 10px 36px var(--shadow1);
}
body.light #inputwrap{background:rgba(255,255,255,0.74)}
#inputwrap:focus-within{border-color:rgba(230,57,70,0.55);box-shadow:0 10px 36px var(--shadow1),0 0 0 3px rgba(230,57,70,0.14)}
#welcome h1{
  background:linear-gradient(115deg,#ffffff 10%,#ff8f9d 45%,#c4b5fd 80%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
body.light #welcome h1{
  background:linear-gradient(115deg,#181820 10%,#c1121f 50%,#6d28d9 85%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
#locbtn,#enhbtn{
  width:36px;height:36px;border-radius:9px;flex-shrink:0;
  background:var(--s3);border:1px solid var(--border2);color:var(--text2);
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:all .15s;
}
#locbtn:hover,#enhbtn:hover{border-color:var(--red);color:var(--red)}
#locbtn svg,#enhbtn svg{width:15px;height:15px}
#enhbtn.busy{opacity:.5;pointer-events:none}
/* map cards */
.map-card{border-radius:14px;overflow:hidden;border:1px solid var(--border2);margin-top:6px}
.map-canvas{height:260px;width:100%;background:var(--s3);cursor:pointer}
.map-meta{padding:10px 14px 12px;background:var(--s2);display:flex;flex-direction:column;gap:8px}
.map-name{font-weight:650;font-size:13.5px}
.map-sub{font-size:12px;color:var(--text2);line-height:1.5}
.wx-line{font-size:13px;color:var(--text)}
.map-row{display:flex;gap:8px;flex-wrap:wrap}
a.map-btn{
  display:inline-flex;align-items:center;gap:6px;
  font-size:12.5px;font-weight:600;color:#fff;text-decoration:none;
  background:linear-gradient(135deg,var(--red),var(--red2));
  padding:7px 14px;border-radius:999px;
}
a.map-btn.ghost{background:var(--s3);color:var(--text);border:1px solid var(--border2)}
.leaflet-container{font-family:var(--font);font-size:12px}
</style>""")

# 3) Composer buttons: location + enhance, before send button
rep('<button id="sendbtn" onclick="send()" aria-label="Send">',
"""<button id="locbtn" onclick="shareLocation()" title="Share my location on a map">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
            </button>
            <button id="enhbtn" onclick="enhancePrompt()" title="Enhance my prompt">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 5.7 5.7 1.9-5.7 1.9L12 18.2l-1.9-5.7L4.4 10.6l5.7-1.9L12 3z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"/></svg>
            </button>
            <button id="sendbtn" onclick="send()" aria-label="Send">""")

# 4) Maps/location JS before textOf()
rep("function textOf(content){",
"""/* ── MAPS / LOCATION / WEATHER ── */
async function mapsApi(payload){
  const res = await fetch('/.netlify/functions/maps',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(payload)
  });
  return res.json();
}
function getPosition(){
  return new Promise((resolve,reject)=>{
    if(!('geolocation' in navigator)) return reject(new Error('Geolocation is not supported on this device.'));
    navigator.geolocation.getCurrentPosition(
      p=>resolve({lat:p.coords.latitude, lon:p.coords.longitude}),
      ()=>reject(new Error('Location permission was denied. Allow location access in your browser and try again.')),
      {timeout:12000, maximumAge:60000}
    );
  });
}
function detectLocationIntent(text){
  const t = text.toLowerCase().trim();
  if(/^(where am i|my location|my current location|locate me|find me|share my location)$/.test(t)) return {type:'me'};
  let m = t.match(/^(?:where is|locate|find|show me(?: on(?: the)? map)?|map of|navigate to|directions to|how (?:do|can) i get to|take me to)\\s+(.+?)[?.!]*$/);
  if(m && m[1].trim()) return {type:'place', query:m[1].trim()};
  m = t.match(/^(?:weather|what's the weather like|what is the weather like)(?: in| at| for)?\\s+(.+?)[?.!]*$/);
  if(m && m[1].trim()) return {type:'weather', query:m[1].trim()};
  return null;
}
function shortName(d){ return String(d||'').split(',').slice(0,2).join(',').trim() || 'Location'; }
let mapSeq = 0;
function addMapMsg(lat, lon, title, sub, weather){
  removeWelcome();
  mapSeq++;
  const mid = 'map-' + mapSeq;
  const wrap = document.createElement('div');
  wrap.className = 'msg ai';
  const wxHtml = weather
    ? `<div class="wx-line">\\u{1F321}\\uFE0F ${weather.tempC}&deg;C &middot; ${esc(weather.description)} &middot; \\u{1F4A7} ${weather.humidity}% humidity &middot; \\u{1F4A8} ${weather.windKph} km/h</div>` : '';
  wrap.innerHTML =
    `<div class="av ai-av">${AI_SVG}</div><div class="mc"><div class="mname">AI Assistant</div>` +
    `<div class="bubble-wrap"><div class="bubble"><div class="map-card">` +
    `<div class="map-canvas" id="${mid}" title="Click to enable scroll-zoom"></div>` +
    `<div class="map-meta"><div class="map-name">${esc(title)}</div>` +
    (sub ? `<div class="map-sub">${esc(sub)}</div>` : '') + wxHtml +
    `<div class="map-row">` +
    `<a class="map-btn" target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&query=${lat},${lon}">Open in Maps</a>` +
    `<a class="map-btn ghost" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}">Get Directions</a>` +
    `</div></div></div></div></div></div>`;
  msgsEl.appendChild(wrap);
  try{
    const map = L.map(mid, {scrollWheelZoom:false}).setView([lat, lon], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      {maxZoom:19, attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
    L.marker([lat, lon]).addTo(map);
    setTimeout(()=>map.invalidateSize(), 120);
    map.on('click', ()=>map.scrollWheelZoom.enable());
  }catch(e){ /* Leaflet failed to load; the map links still work */ }
  const nearBottom = msgsEl.scrollHeight - msgsEl.scrollTop - msgsEl.clientHeight < 200;
  if(nearBottom) scrollToBottom();
  return wrap;
}
async function handleLocationIntent(locIntent, text){
  addMsg('user', text);
  history.push({role:'user', content:text});
  persistCurrent();
  showTyping();
  try{
    if(locIntent.type === 'me'){
      const pos = await getPosition();
      const rev = await mapsApi({action:'reverse', lat:pos.lat, lon:pos.lon});
      hideTyping();
      const label = (rev && rev.displayName) ? rev.displayName : 'Your current location';
      addMapMsg(pos.lat, pos.lon, 'You are here', label, null);
      history.push({role:'assistant', content:`[Map] ${label} (${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)})`});
    }else{
      const g = await mapsApi({action:'geocode', query:locIntent.query});
      hideTyping();
      if(!g || g.error){
        const msg = (g && g.error === 'NOT_FOUND')
          ? `I couldn't find "${locIntent.query}" on the map. Try a more specific place name.`
          : 'The map service is unavailable right now. Try again in a bit.';
        addMsg('ai', msg, true);
        history.push({role:'assistant', content:msg});
      }else{
        let wx = null;
        try{ const w = await mapsApi({action:'weather', lat:g.lat, lon:g.lon}); if(w && !w.error) wx = w; }catch(e){}
        const title = locIntent.type === 'weather' ? ('Weather in ' + shortName(g.displayName)) : shortName(g.displayName);
        addMapMsg(g.lat, g.lon, title, g.displayName, wx);
        history.push({role:'assistant', content:`[Map] ${g.displayName} (${g.lat}, ${g.lon})`});
      }
    }
    persistCurrent();
  }catch(err){
    hideTyping();
    addMsg('ai', err.message || 'Location error.', true);
  }
  sendBtn.disabled = false;
  inputEl.focus();
}
function shareLocation(){
  if(sendBtn.disabled) return;
  inputEl.value = 'my location';
  send();
}
let enhancing = false;
async function enhancePrompt(){
  const text = inputEl.value.trim();
  if(!text || enhancing) return;
  enhancing = true;
  const btn = document.getElementById('enhbtn');
  if(btn) btn.classList.add('busy');
  try{
    const res = await fetch('/.netlify/functions/chat',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({messages:[{role:'user',content:'Rewrite this prompt to be clearer, more specific and more effective for an AI assistant. Return ONLY the rewritten prompt, no quotes, no explanation:\\n\\n' + text}]})
    });
    const data = await res.json();
    if(data && data.reply){
      inputEl.value = data.reply.trim();
      inputEl.style.height = 'auto';
      inputEl.style.height = Math.min(inputEl.scrollHeight, 150) + 'px';
      inputEl.focus();
    }
  }catch(e){}
  enhancing = false;
  if(btn) btn.classList.remove('busy');
}
async function regenerate(wrap){
  const last = history[history.length-1];
  if(!last || last.role !== 'assistant') return;
  if(/^\\[(Map|Image request)\\]/.test(String(last.content||''))) return;
  history.pop();
  if(wrap) wrap.remove();
  showTyping();
  try{
    const res = await fetch('/.netlify/functions/chat',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({messages:history})
    });
    const data = await res.json();
    hideTyping();
    if(data.error){
      addMsg('ai', friendlyError(data.error, false), true);
    }else{
      addMsg('ai', data.reply);
      history.push({role:'assistant', content:data.reply});
      persistCurrent();
    }
  }catch(err){
    hideTyping();
    addMsg('ai', `Connection error: ${err.message}`, true);
  }
}

function textOf(content){""")

# 5) send(): compute locIntent
rep("const useImageGen = !attachment && (imageMode || detectImageIntent(text));",
"""const useImageGen = !attachment && (imageMode || detectImageIntent(text));
  const locIntent = !attachment && !imageMode && !useImageGen && detectLocationIntent(text);""")

# 6) send(): location branch before the normal user message
rep("""  addMsg('user', text);
  history.push({role:'user', content: useImageGen ? `[Image request] ${text}` : text});""",
"""  if(locIntent){
    handleLocationIntent(locIntent, text);
    return;
  }

  addMsg('user', text);
  history.push({role:'user', content: useImageGen ? `[Image request] ${text}` : text});""")

# 7) Regenerate button in addMsg actions
rep("      actions.appendChild(saveBtn);",
"""      actions.appendChild(saveBtn);
      const reBtn = document.createElement('button');
      reBtn.className = 'act-btn';
      reBtn.innerHTML = '\\u21BB Regenerate';
      reBtn.title = 'Regenerate this reply';
      reBtn.onclick = () => regenerate(wrap);
      actions.appendChild(reBtn);""")

# 8) New welcome chips
rep('<button class="chip" onclick="ask(this)">Compare SQL vs NoSQL</button>',
"""<button class="chip" onclick="ask(this)">Compare SQL vs NoSQL</button>
            <button class="chip" onclick="ask(this)">Where is the Eiffel Tower?</button>
            <button class="chip" onclick="ask(this)">Weather in Tokyo</button>""")

# 9) Welcome paragraphs mention maps
rep("image understanding, file generation, or just thinking through a problem together, in any language.",
    "image understanding, file generation, maps &amp; weather, or just thinking through a problem together, in any language.")
rep("<p>Ask me anything — coding, writing, math, analysis, creative work, or just thinking through a problem together.</p>",
    "<p>Ask me anything — coding, writing, math, analysis, creative work, maps &amp; weather, or just thinking through a problem together.</p>")

open(P, "w", encoding="utf-8").write(s)
print("edits applied OK")
