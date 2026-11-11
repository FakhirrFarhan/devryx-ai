P = "/home/hatch/workspace/devryx-ai/public/index.html"
s = open(P, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    assert s.count(old) >= 1, "ANCHOR NOT FOUND: " + old[:80]
    s = s.replace(old, new, count)

# 1) Theme CSS before </style>
rep("</style>",
"""/* ═══════════ INTERFACE THEMES ═══════════ */
#theme-row{display:flex;gap:6px;flex-wrap:wrap}
.theme-opt{
  display:flex;align-items:center;gap:7px;
  background:var(--s2);border:1px solid var(--border2);color:var(--text2);
  font-size:12px;font-weight:600;font-family:var(--font);
  padding:6px 10px 6px 6px;border-radius:999px;cursor:pointer;transition:all .15s;
}
.theme-opt:hover{border-color:var(--text3);color:var(--text)}
.theme-opt.active{border-color:var(--red);color:var(--text);box-shadow:0 0 0 2px var(--bg),0 0 0 3px var(--red)}
.to-prev{width:22px;height:22px;border-radius:50%;flex-shrink:0;border:1px solid rgba(0,0,0,0.2)}

/* ---- Neon Nights: deep black + glowing cyan/magenta ---- */
body[data-theme="neon"]{
  --bg:#04040a;--s1:#0a0a14;--s2:#101020;--s3:#16162a;--s4:#1e1e34;
  --border:rgba(34,211,238,0.10);--border2:rgba(34,211,238,0.22);
  --text:#e8f6ff;--text2:#8fa3c8;--text3:#4a5a7a;
  --red:#22d3ee;--red-rgb:34,211,238;--red2:#0891b2;--red3:#a5f3fc;
  --redbg:rgba(34,211,238,0.08);--redborder:rgba(34,211,238,0.30);
  --green:#34d399;--codebg:#07070f;--codetext:#a5f3fc;
  --headergrad:linear-gradient(135deg,#0a0a18 0%,#0d0d20 50%,#080812 100%);
  --shadow1:rgba(0,0,0,0.5);--shadow2:rgba(0,0,0,0.7);
}
body[data-theme="neon"]::before{
  background:
    radial-gradient(640px 420px at 12% 8%, rgba(34,211,238,0.13), transparent 60%),
    radial-gradient(720px 520px at 88% 18%, rgba(232,121,249,0.12), transparent 60%),
    radial-gradient(860px 620px at 50% 108%, rgba(99,102,241,0.12), transparent 60%);
}
body[data-theme="neon"] #welcome h1{
  background:linear-gradient(115deg,#ffffff 10%,#67e8f9 45%,#f0abfc 80%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
body[data-theme="neon"] .ai .bubble{border-color:rgba(34,211,238,0.18);box-shadow:0 0 24px rgba(34,211,238,0.06)}

/* ---- Paper: warm light editorial ---- */
body[data-theme="paper"]{
  --bg:#f7f3ea;--s1:#fffdf8;--s2:#f1ece0;--s3:#e7dfcf;--s4:#d9cfba;
  --border:rgba(60,40,20,0.10);--border2:rgba(60,40,20,0.16);
  --text:#211a12;--text2:#6b5f4c;--text3:#a89a80;
  --red:#c2410c;--red-rgb:194,65,12;--red2:#9a3412;--red3:#ea7c3c;
  --redbg:rgba(194,65,12,0.08);--redborder:rgba(194,65,12,0.25);
  --green:#15803d;--codebg:#efe9db;--codetext:#3a2f22;
  --headergrad:linear-gradient(135deg,#fffdf8 0%,#f7f3ea 60%,#f1ece0 100%);
  --shadow1:rgba(60,40,20,0.10);--shadow2:rgba(60,40,20,0.16);
}
body[data-theme="paper"]::before{
  background:
    radial-gradient(640px 420px at 12% 8%, rgba(194,65,12,0.06), transparent 60%),
    radial-gradient(720px 520px at 88% 18%, rgba(180,140,60,0.08), transparent 60%),
    radial-gradient(860px 620px at 50% 108%, rgba(154,52,18,0.05), transparent 60%);
}
body[data-theme="paper"] #welcome h1{
  font-family:Georgia,'Times New Roman',serif;letter-spacing:-0.5px;
  background:linear-gradient(115deg,#211a12 20%,#9a3412 60%,#b45309 90%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
body[data-theme="paper"] .bubble{box-shadow:0 2px 10px rgba(60,40,20,0.06)}

/* ---- Deep Ocean: dark navy + teal glass ---- */
body[data-theme="ocean"]{
  --bg:#04121f;--s1:#071a2c;--s2:#0a2338;--s3:#0e2c46;--s4:#123655;
  --border:rgba(56,189,248,0.10);--border2:rgba(56,189,248,0.20);
  --text:#e6f4ff;--text2:#8fb0cc;--text3:#47617d;
  --red:#38bdf8;--red-rgb:56,189,248;--red2:#0284c7;--red3:#7dd3fc;
  --redbg:rgba(56,189,248,0.08);--redborder:rgba(56,189,248,0.28);
  --green:#2dd4bf;--codebg:#03101c;--codetext:#bae6fd;
  --headergrad:linear-gradient(135deg,#071a2c 0%,#0a2338 60%,#04121f 100%);
  --shadow1:rgba(0,0,0,0.45);--shadow2:rgba(0,0,0,0.6);
}
body[data-theme="ocean"]::before{
  background:
    radial-gradient(700px 460px at 12% 8%, rgba(56,189,248,0.12), transparent 60%),
    radial-gradient(760px 540px at 88% 18%, rgba(45,212,191,0.10), transparent 60%),
    radial-gradient(900px 640px at 50% 108%, rgba(29,78,216,0.14), transparent 60%);
}
body[data-theme="ocean"] #welcome h1{
  background:linear-gradient(115deg,#ffffff 10%,#7dd3fc 45%,#5eead4 80%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
body[data-theme="ocean"] #inputwrap{background:rgba(10,35,56,0.66)}
</style>""")

# 2) Theme picker in sidebar footer, after the accent row
rep("""      <div id="sf-divider"></div>
      <div id="sf-legal-links">""",
"""      <div id="sf-divider"></div>
      <div class="sb-foot-label">Interface style</div>
      <div id="theme-row">
        <button class="theme-opt active" data-theme="aurora" title="Aurora (default)">
          <span class="to-prev" style="background:linear-gradient(135deg,#e63946,#8b5cf6,#3b82f6)"></span>Aurora
        </button>
        <button class="theme-opt" data-theme="neon" title="Neon Nights">
          <span class="to-prev" style="background:linear-gradient(135deg,#22d3ee,#e879f9,#6366f1)"></span>Neon
        </button>
        <button class="theme-opt" data-theme="paper" title="Paper">
          <span class="to-prev" style="background:linear-gradient(135deg,#f7f3ea,#e7dfcf,#c2410c)"></span>Paper
        </button>
        <button class="theme-opt" data-theme="ocean" title="Deep Ocean">
          <span class="to-prev" style="background:linear-gradient(135deg,#38bdf8,#2dd4bf,#1d4ed8)"></span>Ocean
        </button>
      </div>
      <div id="sf-divider"></div>
      <div id="sf-legal-links">""")

# 3) toggleTheme: reset to aurora first if a fixed theme is active
rep("""function toggleTheme(){
  const next = document.body.classList.contains('light') ? 'dark' : 'light';""",
"""function toggleTheme(){
  if(document.body.hasAttribute('data-theme')) setInterfaceTheme('aurora');
  const next = document.body.classList.contains('light') ? 'dark' : 'light';""")

# 4) Theme JS before the INIT block
rep("/* ===================== INIT ===================== */",
"""/* ===================== INTERFACE THEMES ===================== */
const IFACE_LABELS = {neon:'Neon Nights', paper:'Paper', ocean:'Deep Ocean'};
function clearAccentOverride(){
  const root = document.documentElement;
  ['--red','--red2','--red3','--red-rgb'].forEach(v=>root.style.removeProperty(v));
}
function setInterfaceTheme(name){
  if(name === 'aurora'){
    document.body.removeAttribute('data-theme');
    applyTheme(localStorage.getItem('ai_theme') === 'light' ? 'light' : 'dark');
  }else{
    document.body.setAttribute('data-theme', name);
    document.body.classList.remove('light');
    clearAccentOverride(); // let the theme's own palette show through
    document.getElementById('theme-icon-dark').style.display = '';
    document.getElementById('theme-icon-light').style.display = 'none';
    const lbl = document.getElementById('theme-label');
    if(lbl) lbl.textContent = IFACE_LABELS[name] || name;
  }
  try{ localStorage.setItem('devryx_iface', name); }catch(e){}
  document.querySelectorAll('.theme-opt').forEach(b=>b.classList.toggle('active', b.dataset.theme===name));
}
document.querySelectorAll('.theme-opt').forEach(btn=>{
  btn.addEventListener('click', ()=> setInterfaceTheme(btn.dataset.theme));
});

/* ===================== INIT ===================== */""")

# 5) Restore saved interface theme at startup (after accent init)
rep("""  } catch(e){
    document.querySelector('.swatch[data-name="Red"]').classList.add('active');
  }
})();
</script>""",
"""  } catch(e){
    document.querySelector('.swatch[data-name="Red"]').classList.add('active');
  }
})();
(function initIface(){
  try{
    const t = localStorage.getItem('devryx_iface');
    if(t && t !== 'aurora') setInterfaceTheme(t);
  }catch(e){}
})();
</script>""")

open(P, "w", encoding="utf-8").write(s)
print("theme switcher applied OK")
