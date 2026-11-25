import os
import re
import sys
import statistics
from collections import defaultdict

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardian.log")

re_scan = re.compile(r"^\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\] SCAN \| .*?NSFW=([\d.]+)%.*?lat=(\d+)ms")
re_fire = re.compile(r"^\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\] FIRE (\S+) \| \S+ \| ([\d.]+)% \| '(.*)'")
re_sem = re.compile(r"^\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\] SEMANTIC BLOCK \| \S+ \| '(.*)'")
re_start = re.compile(r"^\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\] NOT AGAIN .*GUARDIAN ACTIVO")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    only_day = sys.argv[1] if len(sys.argv) > 1 else None
    scans = defaultdict(list)
    fires = defaultdict(list)
    starts = defaultdict(list)

    with open(LOG, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re_scan.match(line)
            if m:
                scans[m.group(1)].append((float(m.group(3)), int(m.group(4))))
                continue
            m = re_fire.match(line)
            if m:
                fires[m.group(1)].append((m.group(2), m.group(3), float(m.group(4)), m.group(5)))
                continue
            m = re_sem.match(line)
            if m:
                fires[m.group(1)].append((m.group(2), "SEMANTICO", None, m.group(3)))
                continue
            m = re_start.match(line)
            if m:
                starts[m.group(1)].append(m.group(2))

    days = sorted(set(scans) | set(fires))
    if only_day:
        days = [d for d in days if d == only_day]
    if not days:
        print("No hay datos para ese dia.")
        return

    for d in days:
        s = scans.get(d, [])
        print("=" * 60)
        print(f"DIA {d}")
        if starts.get(d):
            print("Arranques del guardian:", ", ".join(starts[d]))
        if s:
            vals = [v for v, _ in s]
            lats = [l for _, l in s]
            print(f"Escaneos: {len(s)}")
            print(f"NSFW maximo: {max(vals):.1f}%")
            print(f">=25%: {sum(v >= 25 for v in vals)} | >=50%: {sum(v >= 50 for v in vals)} | >=80%: {sum(v >= 80 for v in vals)}")
            print(f"Latencia mediana: {statistics.median(lats):.0f} ms | Latencia maxima: {max(lats)} ms")
        f_list = fires.get(d, [])
        print(f"Bloqueos: {len(f_list)}")
        for hora, tipo, score, titulo in f_list:
            sc = f"{score:.1f}%" if score is not None else "-"
            print(f"  {hora} | {tipo} | {sc} | {titulo[:60]}")


if __name__ == "__main__":
    main()
