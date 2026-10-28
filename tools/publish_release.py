#!/usr/bin/env python3
"""Publish PDF deliverables as GitHub Release assets (UTF-8 safe names).

Asset names are configured through the ASSETS environment variable, a JSON
list like:
    [{"path": "a.pdf", "name": "a_clean.pdf", "label": "..."}]

Every uploaded asset is downloaded back and its SHA256 compared with the local
file, so a corrupted upload can never go unnoticed. Results land in
ci/release.json.
"""
import hashlib
import json
import mimetypes
import os
import sys
import urllib.parse
import urllib.request

TOKEN = os.environ["GH_TOKEN"]
REPO = os.environ.get("GH_REPO", "AmirGFno/my-files")
TAG = os.environ.get("TAG", "v1")
API = "https://api.github.com"
DELETE_OLD = os.environ.get("DELETE_OLD", "0") == "1"

RELEASE_TITLE = "KECHAP BOOK 1406 — نسخه بدون واترمارک و ترمیم لبه‌ها"
RELEASE_NOTES = (
    "PDF اسکن‌شده کتاب (۲۸۳ صفحه) با حذف کامل واترمارک‌ها.\n\n"
    "دو فایل منتشر شده است:\n"
    "- `..._watermark-free.pdf` — خروجی مرحله ۲: فقط واترمارک حذف شده، "
    "کیفیت اسکن هر صفحه بایت‌به‌بایت دست‌نخورده\n"
    "- `..._edges-repaired.pdf` — خروجی مرحله ۳: همان فایل + سفید شدن نوارهای "
    "سیاه حاشیه اسکن (متن هر صفحه بدون تغییر)\n\n"
    "جزئیات، اعداد اعتبارسنجی و SHA256 در README و validation_report.txt"
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


assets = json.loads(os.environ["ASSETS"])
for a in assets:
    a["sha256"] = sha256_file(a["path"])
    a["size"] = os.path.getsize(a["path"])
    print(f"local: {a['name']} {a['size']} bytes sha256={a['sha256']}", flush=True)

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

# --- drop assets that would collide by name (GitHub rejects duplicates) ----
wanted = {a["name"] for a in assets}
for old in req("GET", f"/repos/{REPO}/releases/{rel['id']}/assets?per_page=100"):
    if DELETE_OLD or old["name"] in wanted:
        req("DELETE", f"/repos/{REPO}/releases/assets/{old['id']}")
        print("removed old asset:", old["name"], flush=True)

# --- upload ----------------------------------------------------------------
for a in assets:
    q = urllib.parse.urlencode({"name": a["name"]})
    up = (f"https://uploads.github.com/repos/{REPO}/releases/{rel['id']}"
          f"/assets?{q}")
    ctype = mimetypes.guess_type(a["path"])[0] or "application/pdf"
    with open(a["path"], "rb") as f:
        payload = f.read()
    r = urllib.request.Request(up, data=payload, method="POST", headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": ctype,
        "Content-Length": str(len(payload)),
        "User-Agent": "arena-agent",
    })
    with urllib.request.urlopen(r, timeout=1800) as resp:
        uploaded = json.loads(resp.read())
    print("uploaded:", uploaded["name"], uploaded["size"],
          uploaded["state"], flush=True)

    # --- verify: download it back and compare sha256 -----------------------
    dreq = urllib.request.Request(
        f"{API}/repos/{REPO}/releases/assets/{uploaded['id']}",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/octet-stream",
                 "User-Agent": "arena-agent"})
    h = hashlib.sha256()
    n = 0
    with urllib.request.urlopen(dreq, timeout=1800) as resp:
        for chunk in iter(lambda: resp.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    a["asset_name"] = uploaded["name"]
    a["asset_size"] = uploaded["size"]
    a["browser_download_url"] = uploaded["browser_download_url"]
    a["sha256_remote"] = h.hexdigest()
    a["bytes_verified"] = n
    a["verified"] = (h.hexdigest() == a["sha256"] and n == a["size"])
    print(f"verified: {a['verified']} ({n} bytes)", flush=True)

info = {
    "release_url": rel["html_url"],
    "tag": TAG,
    "assets": [{k: v for k, v in a.items() if k != "path"} for a in assets],
}
os.makedirs("ci", exist_ok=True)
with open("ci/release.json", "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=2)
print(json.dumps(info, ensure_ascii=False, indent=2))
sys.exit(0 if all(a["verified"] for a in assets) else 4)
