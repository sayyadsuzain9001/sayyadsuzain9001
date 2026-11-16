"""Builds the neofetch-style profile card (assets/card_dark.svg + assets/card_light.svg).

Runs daily in GitHub Actions. Pulls live numbers from the GitHub API:
repos, contributed repos, stars, commits, followers, lines of code (+/-),
and the most recently pushed repo. Set GITHUB_TOKEN for higher rate limits.
Edit config.json to change any of the text on the card.
"""
import json
import os
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
LOGIN = CFG["login"]
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
WIDTH = 58  # characters in the right-hand column


def api(path, method="GET", body=None):
    url = path if path.startswith("http") else f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-card")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return r.status, (json.loads(raw) if raw else None)


def contributor_stats(repo):
    """Commits / additions / deletions by LOGIN. GitHub computes these lazily (HTTP 202), so retry."""
    for _ in range(8):
        status, data = api(f"/repos/{LOGIN}/{repo}/stats/contributors")
        if status == 200 and isinstance(data, list):
            for c in data:
                if c.get("author") and c["author"]["login"].lower() == LOGIN.lower():
                    return c["total"], sum(w["a"] for w in c["weeks"]), sum(w["d"] for w in c["weeks"])
            return 0, 0, 0
        time.sleep(3)
    return 0, 0, 0


def contributed_count():
    if not TOKEN:
        return None
    q = {"query": '{ user(login:"%s") { repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,REPOSITORY]) { totalCount } } }' % LOGIN}
    try:
        _, d = api("https://api.github.com/graphql", "POST", q)
        return d["data"]["user"]["repositoriesContributedTo"]["totalCount"]
    except Exception:
        return None


def ago(iso):
    delta = datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))
    h = int(delta.total_seconds() // 3600)
    if h < 1:
        return "pushed just now"
    return f"{h}h ago" if h < 48 else f"{h // 24}d ago"


def uptime(bday):
    """Age as 'X years, Y months, Z days' from config birthday (YYYY-MM-DD)."""
    if not bday:
        return "coding since 2023"
    b, t = date.fromisoformat(bday), date.today()
    years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    months = (t.month - b.month - (t.day < b.day)) % 12
    y, m = b.year + years, b.month + months
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    anchor = date(y, m, min(b.day, 28))
    days = (t - anchor).days
    return f"{years} years, {months} month{'s' * (months != 1)}, {days} day{'s' * (days != 1)}"


def collect():
    _, user = api(f"/users/{LOGIN}")
    _, repos = api(f"/users/{LOGIN}/repos?per_page=100&type=owner&sort=pushed")
    own = [r for r in repos if not r["fork"] and r["name"].lower() != LOGIN.lower()]
    commits = adds = dels = 0
    for r in own:
        c, a, d = contributor_stats(r["name"])
        commits, adds, dels = commits + c, adds + a, dels + d
    latest = own[0] if own else None
    return {
        "repos": user["public_repos"],
        "contributed": contributed_count(),
        "stars": sum(r["stargazers_count"] for r in repos if not r["fork"]),
        "followers": user["followers"],
        "commits": commits,
        "adds": adds,
        "dels": dels,
        "latest_repo": f"{latest['name']} ({ago(latest['pushed_at'])})" if latest else "-",
    }


# ---------------------------------------------------------------- SVG
THEMES = {
    "dark": dict(bg="#161b22", fg="#c9d1d9", key="#ffa657", val="#a5d6ff", dot="#616e7f", add="#3fb950", rem="#f85149"),
    "light": dict(bg="#f6f8fa", fg="#24292f", key="#953800", val="#0a3069", dot="#c2cfde", add="#1a7f37", rem="#cf222e"),
}


def kv(key, value, width=WIDTH):
    """'. Key: ......... value' padded to an exact width."""
    fill = width - len(key) - len(value) - 5
    return [(".", "dot"), (" ", None), (key, "key"), (":", None), (" " + "." * max(fill, 1) + " ", "dot"), (value, "val")]


def rule(title):
    text = f"- {title} " if title else ""
    return [(text + "-" * (WIDTH - len(text)), None)]


def build_lines(s):
    vals = {"uptime": uptime(CFG.get("birthday")), "latest_repo": s["latest_repo"]}
    head = CFG["header"]
    out = [[(head, None), (" " + "-" * (WIDTH - len(head) - 1), None)]]
    for i, sec in enumerate(CFG["sections"]):
        if i:
            out.append([(".", "dot")])
        out += [kv(k, v.format(**vals)) for k, v in sec]
    out.append([(".", "dot")])
    out.append(rule("Contact"))
    out += [kv(k, v) for k, v in CFG["contact"]]
    out.append([(".", "dot")])
    out.append(rule("GitHub Stats"))
    repos = f"{s['repos']}" + (f" {{Contributed: {s['contributed']}}}" if s["contributed"] is not None else "")
    out.append(kv("Repos", repos, 32) + [(" | ", None)] + kv("Stars", str(s["stars"]), WIDTH - 35)[2:])
    out.append(kv("Commits", f"{s['commits']:,}", 32) + [(" | ", None)] + kv("Followers", str(s["followers"]), WIDTH - 35)[2:])
    net = s["adds"] - s["dels"]
    tail = f"{net:,} ( {s['adds']:,}++, {s['dels']:,}-- )"
    key = "Lines of Code"
    fill = WIDTH - len(key) - len(tail) - 5
    out.append([(".", "dot"), (" ", None), (key, "key"), (":", None), (" " + "." * max(fill, 1) + " ", "dot"),
                (f"{net:,}", "val"), (" ( ", None), (f"{s['adds']:,}++", "add"), (", ", None),
                (f"{s['dels']:,}--", "rem"), (" )", None)])
    return out


def svg(theme, lines, ascii_rows):
    t = THEMES[theme]
    lh, fs, cw = 20, 16, 9.6  # line height, font size, monospace char width
    ascii_cols = max(len(r) for r in ascii_rows)
    ax, tx = 15, 15 + (ascii_cols + 2) * cw
    rows = max(len(lines), len(ascii_rows))
    w, h = int(tx + WIDTH * cw + 15), rows * lh + 25
    ay = 30 + (rows - len(ascii_rows)) * lh // 2  # vertically centre the portrait
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'Courier New\',monospace" width="{w}px" height="{h}px" font-size="{fs}px">',
        '<style>@font-face{src:local("Consolas"),local("Consolas Bold");font-family:"ConsolasFallback";font-display:swap;-webkit-size-adjust:109%;size-adjust:109%}',
        f'.key{{fill:{t["key"]}}}.val{{fill:{t["val"]}}}.dot{{fill:{t["dot"]}}}.add{{fill:{t["add"]}}}.rem{{fill:{t["rem"]}}}text,tspan{{white-space:pre}}</style>',
        f'<rect width="{w}px" height="{h}px" fill="{t["bg"]}" rx="15"/>',
        f'<text x="{ax}" y="{ay}" fill="{t["fg"]}">',
    ]
    for i, row in enumerate(ascii_rows):
        p.append(f'<tspan x="{ax}" y="{ay + i * lh}">{escape(row)}</tspan>')
    p.append(f'</text><text x="{tx}" y="30" fill="{t["fg"]}">')
    for i, segs in enumerate(lines):
        p.append(f'<tspan x="{tx}" y="{30 + i * lh}">')
        p += [f'<tspan class="{c}">{escape(x)}</tspan>' if c else escape(x) for x, c in segs]
        p.append("</tspan>")
    p.append("</text></svg>")
    return "".join(p)


def main():
    stats = collect()
    ascii_rows = (ROOT / "assets" / "ascii.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    lines = build_lines(stats)
    for theme in THEMES:
        (ROOT / "assets" / f"card_{theme}.svg").write_text(svg(theme, lines, ascii_rows), encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
