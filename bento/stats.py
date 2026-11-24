"""GitHub data collection. Stdlib only; every request degrades gracefully."""
import json
import os
import sys
import time
import urllib.request
from datetime import date, datetime, timezone

API = "https://api.github.com"
CACHE_PATH = os.path.join(".bento", "stats.json")
MAX_REPOS_FOR_LINES = 40


def _demo_calendar():
    """Deterministic pseudo-random 53 weeks x 7 days, so example images do not change between builds."""
    out, seed = [], 7
    for w in range(53):
        week = []
        for d in range(7):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            roll = (seed >> 16) % 100
            busy = 1.0 if (w % 9 not in (3, 4) and d not in (0, 6)) else 0.35
            week.append(0 if roll > 62 * busy else (roll % 5) + 1)
        out.append(week)
    return out


def demo(user="octocat"):
    return {
        "profile": {"name": "Octo Cat", "login": user or "octocat", "location": "Madrid", "company": "", "blog": "",
                    "bio": "I build small things for the web and write about them."},
        "username": user or "octocat",
        "updated": date.today().isoformat(),
        "contributions": 312,
        "streak": 6,
        "last20": [0, 2, 1, 0, 0, 3, 4, 1, 0, 2, 5, 1, 0, 0, 2, 3, 1, 4, 2, 1],
        "lines": 48200,
        "repos": 9,
        "stars": 14,
        "followers": 21,
        "following": 12,
        "now": {"repo": "my-project", "message": "add daily stats workflow", "when": "today"},
        "calendar": _demo_calendar(),
        "top_repos": [
            {"name": "bento-readme", "stars": 128, "language": "Python"},
            {"name": "design-tokens", "stars": 54, "language": "TypeScript"},
            {"name": "dotfiles", "stars": 31, "language": "Shell"},
            {"name": "portfolio", "stars": 12, "language": "CSS"},
        ],
        "languages": [["TypeScript", 46.0], ["Python", 24.0], ["CSS", 14.0], ["HTML", 9.0], ["Java", 5.0], ["Shell", 2.0]],
    }


def empty(user):
    """Neutral starting point for a real fetch: never show sample numbers as if they were real."""
    return {
        "username": user, "updated": date.today().isoformat(), "contributions": 0, "streak": 0,
        "last20": [], "lines": 0, "repos": 0, "stars": 0, "followers": 0, "following": 0,
        "now": None, "languages": [], "calendar": [], "top_repos": [], "profile": {},
    }


def load_cache(base_dir="."):
    p = os.path.join(base_dir, CACHE_PATH)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    return {}


def save_cache(stats, base_dir="."):
    p = os.path.join(base_dir, CACHE_PATH)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
        f.write("\n")


class Client:
    def __init__(self, user, token=None, pat=False):
        self.user, self.token, self.pat = user, token, pat

    def call(self, path, body=None):
        url = path if path.startswith("http") else API + path
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "readme-bento"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)


def _safe(fn, default=None):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 - a failing widget must never break the build
        print(f"warn: {e}", file=sys.stderr)
        return default


def _calendar(cl):
    q = """query($u:String!){user(login:$u){followers{totalCount} following{totalCount}
      contributionsCollection{contributionCalendar{totalContributions
      weeks{contributionDays{date contributionCount}}}}}}"""
    _, res = cl.call("/graphql", {"query": q, "variables": {"u": cl.user}})
    return res["data"]["user"]


def _repos(cl):
    out, page = [], 1
    while True:
        path = (f"/user/repos?affiliation=owner&per_page=100&page={page}" if cl.pat
                else f"/users/{cl.user}/repos?type=owner&per_page=100&page={page}")
        _, chunk = cl.call(path)
        out += chunk
        if len(chunk) < 100:
            return [r for r in out if not r["fork"] and r["owner"]["login"].lower() == cl.user.lower()]
        page += 1


def _additions(cl, full_name):
    for _ in range(4):
        status, res = cl.call(f"/repos/{full_name}/stats/contributors")
        if status == 200 and res is not None:
            for c in res:
                if c["author"] and c["author"]["login"].lower() == cl.user.lower():
                    return sum(w["a"] for w in c["weeks"])
            return 0
        time.sleep(3)  # 202: GitHub is still computing the stats
    return 0


def _languages(cl, repos):
    totals = {}
    for r in repos:
        _, langs = cl.call(f"/repos/{r['full_name']}/languages")
        for name, size in (langs or {}).items():
            totals[name] = totals.get(name, 0) + size
    whole = sum(totals.values())
    if not whole:
        return []
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    return [[n, round(100 * s / whole, 1)] for n, s in ranked[:10]]


def _profile(cl):
    _, u = cl.call(f"/users/{cl.user}")
    return {k: (u.get(k) or "") for k in ("name", "login", "bio", "location", "company", "blog")}


def _last_push(cl):
    _, events = cl.call(f"/users/{cl.user}/events/public?per_page=50")
    for e in events:
        if e["type"] == "PushEvent" and e["payload"].get("commits"):
            c = e["payload"]["commits"][-1]
            when = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - when).days
            ago = "today" if days == 0 else "yesterday" if days == 1 else f"{days}d ago"
            return {"repo": e["repo"]["name"].split("/")[-1], "message": c["message"].splitlines()[0][:80], "when": ago}
    return None


def fetch(user, token=None, pat=False, base_dir="."):
    """Returns fresh stats, falling back to cached values for anything that fails."""
    prev = load_cache(base_dir)
    stats = dict(prev) if prev else empty(user)
    stats["username"] = user
    stats["updated"] = date.today().isoformat()
    cl = Client(user, token, pat)

    u = _safe(lambda: _calendar(cl))
    if u:
        cal = u["contributionsCollection"]["contributionCalendar"]
        days = sorted((d for w in cal["weeks"] for d in w["contributionDays"]), key=lambda d: d["date"])
        days = [d for d in days if d["date"] <= date.today().isoformat()]
        counts = [d["contributionCount"] for d in days]
        streak, i = 0, len(counts) - 1
        if i >= 0 and counts[i] == 0:  # today may not have activity yet
            i -= 1
        while i >= 0 and counts[i] > 0:
            streak += 1
            i -= 1
        weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]]
        stats.update(contributions=cal["totalContributions"], streak=streak, last20=counts[-20:], calendar=weeks,
                     followers=u["followers"]["totalCount"], following=u["following"]["totalCount"])

    rs = _safe(lambda: _repos(cl))
    if rs is not None:
        recent = sorted(rs, key=lambda r: r.get("pushed_at") or "", reverse=True)[:MAX_REPOS_FOR_LINES]
        stats["repos"] = len(rs)
        stats["stars"] = sum(r["stargazers_count"] for r in rs)
        # public repos only: a private repository's name must never end up in a public SVG
        public = [r for r in rs if not r.get("private") and not r.get("archived")]
        top = sorted(public, key=lambda r: (-r["stargazers_count"], r.get("pushed_at") or ""))[:8]
        stats["top_repos"] = [{"name": r["name"], "stars": r["stargazers_count"], "language": r.get("language")} for r in top]
        total = sum(_safe(lambda r=r: _additions(cl, r["full_name"]), 0) for r in recent)
        stats["lines"] = max(total, prev.get("lines", 0))  # additions only ever grow
        langs = _safe(lambda: _languages(cl, recent))
        if langs:
            stats["languages"] = langs

    n = _safe(lambda: _last_push(cl))
    if n:
        stats["now"] = n
    prof = _safe(lambda: _profile(cl))
    if prof:
        stats["profile"] = prof
    return stats
