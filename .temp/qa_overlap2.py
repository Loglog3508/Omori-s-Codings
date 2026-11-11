import sys, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.transforms import Bbox

REPORT = []
_orig = Figure.savefig


def patched(self, *a, **k):
    try:
        self.canvas.draw()
        r = self.canvas.get_renderer()
        figbb = self.bbox
        items = []
        for t in self.findobj(Text):
            s = t.get_text()
            if not s or not s.strip() or not t.get_visible():
                continue
            bb = t.get_window_extent(renderer=r)
            if bb.width <= 1 or bb.height <= 1:
                continue
            items.append((s.strip()[:22], bb))
        pairs = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                ov = Bbox.intersection(items[i][1], items[j][1])
                if ov is None:
                    continue
                area = ov.width * ov.height
                if area > 12:
                    pairs.append((round(area), items[i][0], items[j][0]))
        name = str(a[0]).rsplit("\\", 1)[-1] if a else "?"
        pairs.sort(reverse=True)
        REPORT.append((name, len(items), len(pairs), pairs[:6]))
    except Exception as e:
        REPORT.append((str(a[0]) if a else "?", -1, -1, [("ERR", str(e)[:60])]))
    return _orig(self, *a, **k)


Figure.savefig = patched

base = sys.argv[1]
which = sys.argv[2] if len(sys.argv) > 2 else "both"

if which in ("5", "both"):
    spec = importlib.util.spec_from_file_location(
        "lab5", base + "\\\u5b9e\u9a8c\u4e94\\\u5b9e\u9a8c\u4e94.py")
    m5 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m5)
    m5.main()

if which in ("6", "both"):
    spec6 = importlib.util.spec_from_file_location(
        "lab6", base + "\\\u5b9e\u9a8c\u516d\\\u5b9e\u9a8c\u516d.py")
    m6 = importlib.util.module_from_spec(spec6)
    spec6.loader.exec_module(m6)

print("\n===== \u91cd\u53e0\u68c0\u6d4b =====")
total = 0
for name, n, np_, pairs in REPORT:
    total += max(np_, 0)
    print(f"{name}: texts={n} overlap_pairs={np_}")
    for p in pairs:
        print("    OV", p)
print(f"TOTAL_OVERLAP_PAIRS={total}")
