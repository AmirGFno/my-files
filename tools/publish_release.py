#!/usr/bin/env python3
"""Upload the watermark-free PDF as a GitHub Release asset (UTF-8 safe name)
and verify the uploaded bytes against the local SHA256."""
import hashlib
import json
import mimetypes
import os
import sys
import urllib.parse
import urllib.request

TOKEN = os.environ["GH_TOKEN"]
REPO = os.environ.get("GH_REPO", "AmirGFno/my-files")
TAG = "v1"
API = "https://api.github.com"
PDF = sys.argv[1]
RELEASE_TITLE = "KECHAP BOOK 1406 — نسخه بدون واترمارک"
RELEASE_NOTES = (
    "PDF اسکن‌شده کتاب (۲۸۳ صفحه) با حذف کامل واترمارک‌ها.\n\n"
    "- کیفیت اسکن هر صفحه دست‌نخورده (بایت‌های تصویر پایه یکسان با فایل مبدأ)\n"
    "- هیچ بلوک Artifact/Watermark، فونت یا آبجکت XObject واترمارک باقی نمانده "
    "است\n"
    "- جزئیات و SHA256 در README و validation_report.txt"
)


def req(method, path, data=None, headers=None, raw=False):
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "arena-agent",
    }
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = data if raw else json.dumps(data).encode()
        if not raw:
            h["Content-Type"] = "application/json"
    r = urllib.request.Request(API + path, data=body, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=120) as resp:
        payload = resp.read()
    return json.loads(payload) if payload else {}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


name = os.path.basename(PDF)
local_sha = sha256_file(PDF)
size = os.path.getsize(PDF)
print(f"local: {name} {size} bytes sha256={local_sha}", flush=True)

# --- ensure release exists -------------------------------------------------
releases = req("GET", f"/repos/{REPO}/releases?per_page=100")
rel = next((r for r in releases if r["tag_name"] == TAG), None)
if rel is None:
    rel = req("POST", f"/repos/{REPO}/releases", {
        "tag_name": TAG, "target_commitish": "main",
        "name": RELEASE_TITLE, "body": RELEASE_NOTES,
    })
    print("release created:", rel["id"], flush=True)
else:
    rel = req("PATCH", f"/repos/{REPO}/releases/{rel['id']}",
              {"name": RELEASE_TITLE, "body": RELEASE_NOTES})
    print("release updated:", rel["id"], flush=True)

# --- drop old assets -------------------------------------------------------
for a in req("GET", f"/repos/{REPO}/releases/{rel['id']}/assets?per_page=100"):
    req("DELETE", f"/repos/{REPO}/releases/assets/{a['id']}")
    print("deleted old asset:", a["name"], flush=True)

# --- upload ----------------------------------------------------------------
q = urllib.parse.urlencode({"name": name})
up = (f"https://uploads.github.com/repos/{REPO}/releases/{rel['id']}"
      f"/assets?{q}")
ctype = mimetypes.guess_type(name)[0] or "application/pdf"
with open(PDF, "rb") as f:
    payload = f.read()
r = urllib.request.Request(up, data=payload, method="POST", headers={
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": ctype,
    "Content-Length": str(len(payload)),
    "User-Agent": "arena-agent",
})
with urllib.request.urlopen(r, timeout=1800) as resp:
    asset = json.loads(resp.read())
print("uploaded:", asset["name"], asset["size"], asset["state"], flush=True)

# --- verify: download it back and compare sha256 ---------------------------
dreq = urllib.request.Request(
    f"{API}/repos/{REPO}/releases/assets/{asset['id']}",
    headers={"Authorization": f"Bearer {TOKEN}",
             "Accept": "application/octet-stream",
             "User-Agent": "arena-agent"})
h = hashlib.sha256()
n = 0
with urllib.request.urlopen(dreq, timeout=1800) as resp:
    for chunk in iter(lambda: resp.read(1 << 20), b""):
        h.update(chunk)
        n += len(chunk)
remote_sha = h.hexdigest()
ok = (remote_sha == local_sha and n == size)
print(f"remote: {n} bytes sha256={remote_sha} match={ok}", flush=True)

info = {
    "asset_name": asset["name"],
    "asset_size": asset["size"],
    "asset_state": asset["state"],
    "browser_download_url": asset["browser_download_url"],
    "release_url": rel["html_url"],
    "sha256_local": local_sha,
    "sha256_remote": remote_sha,
    "bytes_verified": n,
    "verified": ok,
}
os.makedirs("ci", exist_ok=True)
with open("ci/release.json", "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=2)
print(json.dumps(info, ensure_ascii=False, indent=2))
sys.exit(0 if ok else 4)
