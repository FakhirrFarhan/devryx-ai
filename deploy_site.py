#!/usr/bin/env python3
"""Deploy the Devryx AI production site (static + functions) to Netlify.

Site: devryxai (67fa6f48-976a-48ff-8e0c-0f8720ff6cc0)
Static files come from public/, functions from netlify/functions/ (zipped).
Env vars (GROQ_API_KEY etc.) already live on the site as production secrets;
a redeploy does not touch them. netlify.toml is uploaded at / so the
per-function timeout config ([functions.chat] timeout=26) is honored.
"""
import sys, os, json, hashlib, zipfile, io, time
import urllib.request
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

BASE = "https://api.netlify.com/api/v1"
CRED = "custom.netlify"
HOSTS = ["api.netlify.com"]
SITE_ID = "67fa6f48-976a-48ff-8e0c-0f8720ff6cc0"
ROOT = os.path.dirname(os.path.abspath(__file__))

def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    add_surrogate_to_request(r, CRED, allowed_hosts=HOSTS)
    with urllib.request.urlopen(r, timeout=60) as resp:
        return read_json_response(resp)

def put_raw(url, data, ctype):
    req = urllib.request.Request(url, data=data, method="PUT",
                                 headers={"Content-Type": ctype})
    add_surrogate_to_request(req, CRED, allowed_hosts=HOSTS)
    # function ZIP PUTs can 500 transiently — retry a few times
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                resp.read()
            return
        except Exception as e:
            if attempt == 3:
                raise
            print(f"  PUT retry {attempt+1} ({e})")
            time.sleep(5)

def sha1_file(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

# 1. static files from public/
pub = os.path.join(ROOT, "public")
files = {}
for dirpath, _, fns in os.walk(pub):
    for fn in fns:
        full = os.path.join(dirpath, fn)
        rel = "/" + os.path.relpath(full, pub).replace(os.sep, "/")
        files[rel] = sha1_file(full)
# netlify.toml at root so function timeout config applies
toml = os.path.join(ROOT, "netlify.toml")
files["/netlify.toml"] = sha1_file(toml)

# 2. zip each function (stdlib-only, like the demo relay)
funcs = {}
fdir = os.path.join(ROOT, "netlify", "functions")
for fn in sorted(os.listdir(fdir)):
    if not fn.endswith(".js"):
        continue
    name = fn[:-3]
    with open(os.path.join(fdir, fn)) as f:
        code = f.read()
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(fn, code)
    zb = zbuf.getvalue()
    funcs[name] = (hashlib.sha256(zb).hexdigest(), zb)

dep = api("POST", f"/sites/{SITE_ID}/deploys", {
    "files": files,
    "functions": {n: s for n, (s, _) in funcs.items()},
    "async": True,
})
dep_id = dep["id"]
print("deploy:", dep_id)

# 3. upload static files (only those Netlify still needs)
need = set(dep.get("required", []) or [])
for rel, sha in files.items():
    if sha not in need:
        continue
    full = os.path.join(pub, rel.lstrip("/")) if rel != "/netlify.toml" else toml
    put_raw(f"{BASE}/deploys/{dep_id}/files{rel}", open(full, "rb").read(),
            "application/octet-stream")
print("static uploads done")

# 4. upload function zips
for name, (sha, zb) in funcs.items():
    put_raw(f"{BASE}/deploys/{dep_id}/functions/{name}?runtime=js", zb,
            "application/zip")
    print("function uploaded:", name)

# 5. wait for ready
for _ in range(30):
    d = api("GET", f"/deploys/{dep_id}")
    if d.get("state") == "ready":
        break
    if d.get("state") == "error":
        raise SystemExit(f"deploy error: {d.get('error_message')}")
    time.sleep(10)
print("state:", d.get("state"))
print("LIVE: https://devryxai.netlify.app")
