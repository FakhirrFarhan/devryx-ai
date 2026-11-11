P = "/home/hatch/workspace/devryx-ai/public/index.html"
s = open(P, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, "ANCHOR count=%d want %d: %s" % (s.count(old), count, old[:90])
    s = s.replace(old, new)

# ── 1) CSS ──
rep("</style>",
"""/* ═══════════ MUSE-LIKE: follow-ups, voice chat, memory ═══════════ */
.followups{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.fu-chip{background:var(--s3);border:1px solid var(--border2);color:var(--text1);border-radius:999px;padding:6px 12px;font-size:12px;font-family:var(--font);cursor:pointer;transition:all .15s}
.fu-chip:hover{border-color:var(--red);color:var(--red)}
#voicechatbtn.on{background:linear-gradient(135deg,var(--red),var(--red2));border-color:var(--red);color:#fff;box-shadow:0 0 10px rgba(var(--red-rgb),0.5)}
#mem-name{width:100%;box-sizing:border-box;background:var(--s3);border:1px solid var(--border2);color:var(--text1);border-radius:8px;padding:7px 10px;font-size:12.5px;font-family:var(--font);outline:none;margin-top:2px}
#mem-name:focus{border-color:var(--red)}
#mem-name::placeholder{color:var(--text2)}
</style>""")

# ── 2) Header: voice-chat button after the Voice button ──
rep("""          Voice
        </button>""",
"""          Voice
        </button>
        <button class="hbtn" id="voicechatbtn" onclick="toggleVoiceChat()" title="Hands-free voice conversation">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0118 0v6"/><path d="M21 19a2 2 0 01-2 2h-1a2 2 0 01-2-2v-3a2 2 0 012-2h3v5zM3 19a2 2 0 002 2h1a2 2 0 002-2v-3a2 2 0 00-2-2H3v5z"/></svg>
          Voice chat
        </button>""")

# ── 3) Sidebar footer: memory input before legal links ──
rep('<div id="sf-legal-links">',
"""<div id="sf-divider"></div>
      <div class="sb-foot-label">About you</div>
      <input id="mem-name" type="text" maxlength="40" placeholder="Your name — I'll remember you" autocomplete="off">
      <div id="sf-divider"></div>
      <div id="sf-legal-links">""")

# ── 4) Muse-like JS section before the video section ──
rep("/* ── VIDEO GENERATION (free Zeroscope model via public HF Space) ── */",
"""/* ── MUSE-LIKE: memory, follow-up suggestions, voice conversation ── */
let userMemory = {name:''};
try{ userMemory = Object.assign({name:''}, JSON.parse(localStorage.getItem('devryx_memory')||'{}')); }catch(e){}
function saveMemory(){ try{ localStorage.setItem('devryx_memory', JSON.stringify(userMemory)); }catch(e){} }
function personalizeWelcome(){
  const h1 = document.querySelector('#welcome h1');
  if(h1) h1.textContent = userMemory.name ? `Hey ${userMemory.name} \\u2014 let\\u2019s figure this out.` : "Let\\u2019s figure this out.";
}
const memNameInput = document.getElementById('mem-name');
if(memNameInput){
  memNameInput.value = userMemory.name || '';
  const commitName = ()=>{
    userMemory.name = memNameInput.value.trim().slice(0,40);
    saveMemory(); personalizeWelcome();
  };
  memNameInput.addEventListener('change', commitName);
  memNameInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter'){ commitName(); memNameInput.blur(); } });
}
personalizeWelcome();

function splitFollowups(reply){
  const parts = String(reply||'').split('|||');
  if(parts.length < 4) return {text: reply, follows: []};
  const follows = parts.slice(1,4).map(x=>x.trim()).filter(Boolean);
  if(!follows.length) return {text: reply, follows: []};
  return {text: parts[0].replace(/\\s+$/,''), follows};
}
function addFollowupChips(aiWrap, follows){
  if(!aiWrap || !follows || !follows.length) return;
  const bwrap = aiWrap.querySelector('.bubble-wrap');
  if(!bwrap || bwrap.querySelector('.followups')) return;
  const row = document.createElement('div');
  row.className = 'followups';
  follows.forEach(q=>{
    const b = document.createElement('button');
    b.className = 'fu-chip';
    b.textContent = q;
    b.onclick = ()=>{ inputEl.value = q; inputEl.dispatchEvent(new Event('input')); send(); };
    row.appendChild(b);
  });
  bwrap.appendChild(row);
}

let voiceChat = false;
const voiceChatBtn = document.getElementById('voicechatbtn');
function toggleVoiceChat(){
  voiceChat = !voiceChat;
  voiceChatBtn.classList.toggle('on', voiceChat);
  if(voiceChat){
    if(!('speechSynthesis' in window) || !(window.SpeechRecognition || window.webkitSpeechRecognition)){
      alert('Voice chat needs speech recognition + speech synthesis (Chrome or Edge).');
      voiceChat = false; voiceChatBtn.classList.remove('on'); return;
    }
    if(speechSynthesis.speaking) speechSynthesis.cancel();
    autoSpeak = true; voiceBtn.classList.add('active');
    hintEl.innerHTML = 'Voice chat is ON \\u2014 just talk, I\\u2019ll listen and reply out loud &nbsp;·&nbsp; Click again to stop';
    startVoiceListen();
  }else{
    stopVoiceListen();
    if(speechSynthesis.speaking) speechSynthesis.cancel();
    autoSpeak = false; voiceBtn.classList.remove('active');
    hintEl.innerHTML = 'Enter to send &nbsp;·&nbsp; Shift+Enter for new line';
  }
}
function startVoiceListen(){
  if(!voiceChat) return;
  if(!recognition) recognition = setupRecognition();
  if(!recognition) return;
  try{
    listening = true;
    micBtn.classList.add('on'); inputWrap.classList.add('listening');
    recognition.start();
  }catch(e){}
}
function stopVoiceListen(){
  listening = false;
  try{ micBtn.classList.remove('on'); inputWrap.classList.remove('listening'); }catch(e){}
  try{ if(recognition) recognition.stop(); }catch(e){}
}
function speakReplyAloud(text, onDone){
  if(!('speechSynthesis' in window)){ if(onDone) onDone(); return; }
  speechSynthesis.cancel();
  const plain = String(text||'').replace(/```[\\s\\S]*?```/g,' code block ').replace(/[#*`>_-]/g,'').slice(0, 600);
  const u = new SpeechSynthesisUtterance(plain);
  u.onend = ()=>{ if(onDone) onDone(); };
  u.onerror = ()=>{ if(onDone) onDone(); };
  speechSynthesis.speak(u);
}
function voiceChatResumeListen(){
  if(!voiceChat) return;
  setTimeout(()=>{ startVoiceListen(); }, 500);
}

/* ── VIDEO GENERATION (free Zeroscope model via public HF Space) ── */""")

# ── 5) recognition onresult: auto-send on final result in voice-chat mode ──
rep("""  r.onresult = (e)=>{
    let transcript = '';
    for(let i=0;i<e.results.length;i++) transcript += e.results[i][0].transcript;
    inputEl.value = transcript;
    inputEl.dispatchEvent(new Event('input'));
  };""",
"""  r.onresult = (e)=>{
    let transcript = '';
    let isFinal = false;
    for(let i=0;i<e.results.length;i++){ transcript += e.results[i][0].transcript; if(e.results[i].isFinal) isFinal = true; }
    inputEl.value = transcript;
    inputEl.dispatchEvent(new Event('input'));
    if(voiceChat && isFinal && transcript.trim()){
      stopVoiceListen();
      setTimeout(()=>{ if(voiceChat && inputEl.value.trim()) send(); }, 350);
    }
  };""")

# ── 6a) Chat branch 1 (attachment flow): follow-ups + voice-chat speech ──
rep("""      } else {
        addMsg('ai', data.reply);
        history.push({role:'assistant', content:data.reply});
        persistCurrent();
        if(autoSpeak) speakText(null, data.reply);
      }""",
"""      } else {
        const sf = splitFollowups(data.reply);
        const aw = addMsg('ai', sf.text);
        addFollowupChips(aw, sf.follows);
        history.push({role:'assistant', content:sf.text});
        persistCurrent();
        if(voiceChat) speakReplyAloud(sf.text, voiceChatResumeListen);
        else if(autoSpeak) speakText(null, sf.text);
      }""")

# ── 6b) Chat branch 2 (plain flow): follow-ups + voice-chat speech ──
rep("""    } else {
      addMsg('ai', data.reply);
      history.push({role:'assistant', content:data.reply});
      persistCurrent();
      if(autoSpeak) speakText(null, data.reply);
    }""",
"""    } else {
      const sf = splitFollowups(data.reply);
      const aw = addMsg('ai', sf.text);
      addFollowupChips(aw, sf.follows);
      history.push({role:'assistant', content:sf.text});
      persistCurrent();
      if(voiceChat) speakReplyAloud(sf.text, voiceChatResumeListen);
      else if(autoSpeak) speakText(null, sf.text);
    }""")

# ── 7) All chat POSTs carry memory ──
rep("body:JSON.stringify({messages:history})",
    "body:JSON.stringify({messages:history, memory:userMemory})", count=3)

# ── 8) regenerate(): follow-up chips too ──
rep("""    }else{
      addMsg('ai', data.reply);
      history.push({role:'assistant', content:data.reply});
      persistCurrent();
    }""",
"""    }else{
      const sf = splitFollowups(data.reply);
      const aw = addMsg('ai', sf.text);
      addFollowupChips(aw, sf.follows);
      history.push({role:'assistant', content:sf.text});
      persistCurrent();
    }""")

# ── 9) Image branch: resume voice listening when done ──
rep("""    sendBtn.disabled = false;
    inputEl.focus();
    return;
  }

  try{""",
"""    sendBtn.disabled = false;
    inputEl.focus();
    voiceChatResumeListen();
    return;
  }

  try{""")

# ── 10) Video branch end: resume voice listening ──
rep("""  sendBtn.disabled = false;
  inputEl.focus();
}
function setStatusSafe(prog, t){ try{ prog.setStatus(t); }catch(e){} }""",
"""  sendBtn.disabled = false;
  inputEl.focus();
  voiceChatResumeListen();
}
function setStatusSafe(prog, t){ try{ prog.setStatus(t); }catch(e){} }""")

# ── 11) Location branch end: resume voice listening ──
rep("""  sendBtn.disabled = false;
  inputEl.focus();
}
function shareLocation(){""",
"""  sendBtn.disabled = false;
  inputEl.focus();
  voiceChatResumeListen();
}
function shareLocation(){""")

# ── 12) Sender name: AI Assistant -> Devryx ──
rep("name.textContent = role==='ai' ? 'AI Assistant' : 'You';",
    "name.textContent = role==='ai' ? 'Devryx' : 'You';")
rep(">AI Assistant</div>", ">Devryx</div>", count=3)
rep("[${m.role === 'user' ? 'You' : 'AI Assistant'}]", "[${m.role === 'user' ? 'You' : 'Devryx'}]")

# ── 13) newChat welcome h1: personalized ──
rep("""    <h1>Let's figure this out.</h1>
    <p>Ask me anything — coding, writing, math, analysis, creative work, maps &amp; weather, or just thinking through a problem together.</p>""",
"""    <h1>${userMemory.name ? `Hey ${esc(userMemory.name)} — let's figure this out.` : "Let's figure this out."}</h1>
    <p>Ask me anything — coding, writing, math, analysis, creative work, maps &amp; weather, or just thinking through a problem together.</p>""")

open(P, "w", encoding="utf-8").write(s)
print("muse-like UI applied OK")
