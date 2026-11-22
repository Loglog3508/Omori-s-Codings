# -*- coding: utf-8 -*-
"""把 Stata esttab 输出的 rtf 表格渲染成纯文本，便于核对。"""
import re
import sys

W = r"C:\Users\omori\Omori-s-Codings\课程\计量经济分析\输出"


def unescape_rtf_u(s: str) -> str:
    """处理 esttab 的 \\uXXXX? 形式（十进制码点带 ? 占位）。"""
    def repl(m):
        n = int(m.group(1))
        if n < 0:
            n += 65536
        return chr(n)
    s = re.sub(r"\\u(-?\d+)\?", repl, s)
    return s


def rtf_to_text(raw: str) -> str:
    raw = unescape_rtf_u(raw)
    raw = re.sub(r"\\par[d]?\s*", "\n", raw)
    raw = re.sub(r"\\cell\s*", " | ", raw)
    raw = re.sub(r"\\row\s*", "\n", raw)
    raw = re.sub(r"\\tab\s*", "\t", raw)
    # 去掉其余控制字
    raw = re.sub(r"\\[a-zA-Z]+-?\d*\s?", "", raw)
    raw = raw.replace("{", "").replace("}", "").replace("\\", "")
    lines = [ln.rstrip() for ln in raw.split("\n")]
    return "\n".join(ln for ln in lines if ln.strip())


for fn in sys.argv[1:] or ["表2_回归对比", "表3_加法模型", "表4_乘法模型"]:
    with open(f"{W}\\{fn}.rtf", "rb") as f:
        raw = f.read().decode("latin-1")
    print("=" * 30, fn)
    print(rtf_to_text(raw))
