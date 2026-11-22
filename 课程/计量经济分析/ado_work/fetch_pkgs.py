# -*- coding: utf-8 -*-
"""把 SSC 上的 ftools / reghdfe / center 包直接下载到本地 ado 目录（绕开 Stata 的写权限问题）。"""
import os
import re
import urllib.request

TARGET = r"C:\Users\omori\Omori-s-Codings\课程\计量经济分析\ado_work"
BASE = "http://repec.org/bocode/"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Stata/18"})
    return urllib.request.urlopen(req, timeout=60).read()


def fetch_pkg(name):
    txt = get(f"{BASE}{name[0]}/{name}.pkg").decode("latin-1")
    # pkg 文件里每行形如 "f filename" 或 "f ../j/join.ado"
    names = re.findall(r"^f\s+(\S+)\s*$", txt, re.M)
    for raw in names:
        sub = os.path.dirname(raw).strip("./")
        base = os.path.basename(raw)
        if sub.startswith(".."):
            sub = sub.strip(".").strip("/")
        if not sub:
            sub = name[0]
        url = f"{BASE}{sub}/{base}"
        try:
            data = get(url)
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL {raw} ({url}) {type(e).__name__}")
            continue
        out = os.path.join(TARGET, sub, base)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(data)
        print(f"  ok {sub}/{base} {len(data)} bytes")


for pkg in ["ftools", "reghdfe", "center"]:
    print("===", pkg)
    fetch_pkg(pkg)
print("done", TARGET)
