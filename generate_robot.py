"""Generates robot.svg: a little robot that rolls across your GitHub
contribution graph and smashes every green square, then it all resets."""
import json, os, sys, urllib.request

STEP, CELL = 15, 12
PAD_X, PAD_Y = 24, 24
EMPTY = "#161b22"
LEVELS = ["#0e4429", "#006d32", "#26a641", "#39d353"]
SEC_PER_TARGET, LEAD, HOLD = 0.14, 1.0, 2.5

QUERY = """query($u:String!){user(login:$u){contributionsCollection{
contributionCalendar{weeks{contributionDays{contributionCount weekday}}}}}}"""

def fetch(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"u": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req))
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[d["contributionCount"] for d in w["contributionDays"]] for w in weeks]

def level(c, mx):
    if c <= 0: return -1
    return min(3, int((c / mx) * 4 - 1e-9))

def build(weeks):
    mx = max([c for w in weeks for c in w] + [1])
    pos = lambda wi, di: (PAD_X + wi * STEP + CELL / 2, PAD_Y + di * STEP + CELL / 2)
    targets = []
    for wi, w in enumerate(weeks):
        days = range(len(w)) if wi % 2 == 0 else reversed(range(len(w)))
        targets += [(wi, di) for di in days if w[di] > 0]
    n = len(targets)
    total = LEAD + n * SEC_PER_TARGET + HOLD
    W = PAD_X * 2 + len(weeks) * STEP
    H = PAD_Y * 2 + 7 * STEP
    arrive = {t: (LEAD + (i + 1) * SEC_PER_TARGET) / total for i, t in enumerate(targets)}

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" rx="8" fill="#0d1117"/>']
    for wi, w in enumerate(weeks):
        for di, c in enumerate(w):
            x, y = PAD_X + wi * STEP, PAD_Y + di * STEP
            lv = level(c, mx)
            if lv < 0:
                out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{EMPTY}"/>')
                continue
            t = arrive[(wi, di)]
            e = min(t + 0.004, 0.999); e2 = min(t + 0.02, 0.9995)
            col = LEVELS[lv]
            out.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{col}">'
                f'<animate attributeName="fill" dur="{total:.2f}s" repeatCount="indefinite" '
                f'values="{col};{col};#ff4d4d;{EMPTY};{EMPTY}" keyTimes="0;{t:.5f};{e:.5f};{e2:.5f};1"/></rect>')

    # robot path
    pts = [(-20, pos(*targets[0])[1] if targets else H / 2)] if n else [(-20, H / 2)]
    times = [0.0]
    for i, t in enumerate(targets):
        pts.append(pos(*t)); times.append(arrive[t])
    last_y = pts[-1][1]
    pts.append((W + 20, last_y)); times.append(min((LEAD + n * SEC_PER_TARGET + 0.8) / total, 0.999))
    pts.append((W + 20, last_y)); times.append(1.0)
    values = ";".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    kt = ";".join(f"{t:.5f}" for t in times)
    out.append(
        '<g><animateTransform attributeName="transform" type="translate" '
        f'dur="{total:.2f}s" repeatCount="indefinite" values="{values}" keyTimes="{kt}"/>'
        '<line x1="0" y1="-9" x2="0" y2="-13" stroke="#9aa4ff" stroke-width="1.5"/>'
        '<circle cx="0" cy="-14" r="2" fill="#ff4d4d"/>'
        '<rect x="-9" y="-9" width="18" height="15" rx="4" fill="#9aa4ff" stroke="#0d1117" stroke-width="1.5"/>'
        '<rect x="-6" y="-5" width="4" height="4" rx="1" fill="#0d1117"/>'
        '<rect x="2" y="-5" width="4" height="4" rx="1" fill="#0d1117"/>'
        '<rect x="-5" y="-4" width="2" height="2" fill="#00e5ff"/>'
        '<rect x="3" y="-4" width="2" height="2" fill="#00e5ff"/>'
        '<rect x="-5" y="6" width="4" height="3" rx="1.5" fill="#555"/>'
        '<rect x="1" y="6" width="4" height="3" rx="1.5" fill="#555"/></g>')
    out.append("</svg>")
    return "\n".join(out)

if __name__ == "__main__":
    user = os.environ.get("GH_USER", "DikshantDuggal")
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        import random; random.seed(1)
        weeks = [[random.choice([0, 0, 0, 1, 2, 4, 7]) for _ in range(7)] for _ in range(53)]
    else:
        weeks = fetch(user, os.environ["GITHUB_TOKEN"])
    os.makedirs("dist", exist_ok=True)
    open("dist/robot.svg", "w").write(build(weeks))
    print("wrote dist/robot.svg")
