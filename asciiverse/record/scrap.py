"""Scrap preview: a robot exploring, shooting enemy robots and salvaging
their wrecks.

Scrap's 80x25 screen is centred whole in the 100x30 recording, so it
starts at row 2, column 10: the message line, then the 48x24 map on the
left and the robot's eight system slots on the right. The driver reads
the map, and with an enemy (a letter) within range fires its first
working weapon at it (the game picks the nearest target); walks to each
wreck (%) and salvages a weapon, sensor or armour from it into an empty
slot; otherwise explores towards the nearest unseen ground, and after a
while takes the exit (>) to the next level. It answers the More prompts.
After about 50 seconds it quits, and the cast ends on the game's own
"play again?" answered no. A take where the robot is destroyed early is
recorded again.

    python3 asciiverse/record/scrap.py

For a long test run of another build (an ASan one, say), without
touching the preview:

    python3 asciiverse/record/scrap.py --soak 600 --bindir /tmp/asan
"""
import argparse, collections, heapq, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec

OY, OX = 2, 10          # where the centred 80x25 screen sits in 100x30
MAPH, MAPW = 24, 48
STEP = {(-1, 0): "k", (1, 0): "j", (0, -1): "h", (0, 1): "l",
        (-1, -1): "y", (-1, 1): "u", (1, -1): "b", (1, 1): "n"}
# what a two-wheel drive can cross, and at what cost; rough ground is slow
COST = {".": 1, ":": 1, ">": 1, "?": 1, "-": 2, "!": 4}
# every weapon and its range, from the Weapon(...) lines in being.cpp
RANGE = {"automatic gun": 3, "bazooka": 4, "bomb array": 2, "cold ray": 6,
         "disrupter": 1, "extended gun": 4, "extended heavy gun": 4,
         "fireball": 6, "flamethrower": 3, "grinder": 1, "gun": 2,
         "heavy flamethrower": 5, "heavy gun": 3, "heavy torpedo tube": 8,
         "lightning bolt": 6, "long-range artillery": 16, "medium gun": 2,
         "minigun": 1, "phaser rifle": 2, "quake engine": 3, "shredder": 1,
         "sonic gun": 2, "steelshredder": 1, "taser": 1, "torpedo tube": 3,
         "weak laser gun": 2}
WANTED = re.compile(r"gun|laser|rifle|bazooka|ray|flamethrower|shredder|minigun|"
                    r"sensor|scope|radar|plating|armor|shield")


def grid(r):
    rows = r.rows()
    return [rows[OY + y][OX:OX + 80] for y in range(25)]


def slots(g):
    """The eight slots on the right: (name, percent), name '' when empty."""
    out = []
    for i in range(8):
        line = g[1 + 3 * i][50:80].strip()
        name = line[2:].strip() if len(line) > 2 and line[0].isdigit() else ""
        m = re.search(r"(\d+)%", g[2 + 3 * i][50:80])
        out.append((name, int(m.group(1)) if m else 0))
    return out


def find_player(g):
    for x in range(MAPH):
        y = g[1 + x].find("@", 0, MAPW)
        if y >= 0:
            return x, y
    return None


def cell(g, x, y):
    return g[1 + x][y]


def route(g, start, goal, blocked, goal_passable=True):
    """First step of the cheapest 8-way path to a cell where goal(x, y)."""
    best = {start: 0}
    first = {start: None}
    q = [(0, start)]
    while q:
        d, (x, y) = heapq.heappop(q)
        if d > best[(x, y)]:
            continue
        if (x, y) != start and goal(x, y):
            return first[(x, y)]
        for (dx, dy) in STEP:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < MAPH and 0 <= ny < MAPW) or (nx, ny) in blocked:
                continue
            c = cell(g, nx, ny)
            cost = COST.get(c)
            if cost is None:
                if goal_passable or not goal(nx, ny):
                    continue
                cost = 1
            nd = d + cost
            if nd < best.get((nx, ny), 1 << 30):
                best[(nx, ny)] = nd
                first[(nx, ny)] = first[(x, y)] or (dx, dy)
                heapq.heappush(q, (nd, (nx, ny)))
    return None


def play(r, limit, descend_after, log=None):
    """Plays until limit seconds; returns 'quit' or 'dead'."""
    blocked = set()
    tried_wrecks = set()
    visits = collections.Counter()
    level_start = r.elapsed()
    cooldown = 0
    exit_at = None
    last_target = 0
    shown = 0
    while r.elapsed() < limit:
        g = grid(r)
        msg = g[0]
        if DEBUG and r.elapsed() - shown > DEBUG:
            shown = r.elapsed()
            print(f"--- {shown:.0f} s", *g, sep="\n", file=sys.stderr)
        if "More" in msg[70:]:
            r.key(" ", 0.25)
            continue
        if "play again" in msg:
            return "dead"
        if "Press any key" in msg:
            r.key(" ", 0.2)
            continue
        if "You go to level" in msg:
            blocked.clear()
            tried_wrecks.clear()
            visits.clear()
            exit_at = None
            level_start = r.elapsed()
        if "Which system do you want to salvage" in msg:
            pick = next((i for i, (n, p) in enumerate(slots(g)) if n and WANTED.search(n) and p > 50),
                        None)
            r.key(str(pick + 1) if pick is not None else "x", 0.3)
            continue
        if "in which slot?" in msg:
            empty = next((i for i, (n, p) in enumerate(slots(g)) if not n), None)
            r.key(str(empty + 1) if empty is not None else "x", 0.3)
            continue
        if "Invalid target" in msg:
            # the last target is out of the weapon's range: close in first
            r.key("x", 0.15)
            cooldown = 4
            last_target = 0
            continue
        if "Use +/-" in msg:
            if last_target:
                r.key("x", 0.15)
                cooldown = 6
                last_target = 0
            else:
                r.key("f", 0.35)
                last_target = 1
            continue
        last_target = 0
        if "(y/n)" in msg:
            r.key("n", 0.2)
            continue
        me = find_player(g)
        if me is None:
            r.key(".", 0.2)
            continue
        x, y = me
        visits[me] += 1
        if "can't go there" in msg and getattr(play, "aim", None):
            blocked.add(play.aim)
        play.aim = None
        for ex in range(MAPH):
            ey = g[1 + ex].find(">", 0, MAPW)
            if ey >= 0:
                exit_at = (ex, ey)
        foes = [(ex, ey) for ex in range(MAPH) for ey in range(MAPW)
                if cell(g, ex, ey).isalpha()]
        near = [f for f in foes if max(abs(f[0] - x), abs(f[1] - y)) <= 6]
        mine = slots(g)
        guns = [(RANGE[n], i) for i, (n, p) in enumerate(mine) if n in RANGE and p > 50]
        reach, gun = max(guns) if guns else (0, None)
        dist = min((max(abs(f[0] - x), abs(f[1] - y)) for f in near), default=99)
        if cooldown:
            cooldown -= 1
        if "shooting yourself" in msg:
            # nothing in the weapon's range: close in first
            cooldown = 4
        if near and gun is not None and dist <= reach and not cooldown:
            r.key(str(gun + 1), 0.25)
            continue
        step = None
        if near and gun is not None:
            f = min(near, key=lambda p: max(abs(p[0] - x), abs(p[1] - y)))
            step = route(g, me, lambda a, b: max(abs(a - f[0]), abs(b - f[1])) <= 1, blocked)
        wrecks = [(wx, wy) for wx in range(MAPH) for wy in range(MAPW)
                  if cell(g, wx, wy) == "%" and (wx, wy) not in tried_wrecks]
        if wrecks and step is None:
            w = min(wrecks, key=lambda p: max(abs(p[0] - x), abs(p[1] - y)))
            if max(abs(w[0] - x), abs(w[1] - y)) == 1:
                tried_wrecks.add(w)
                r.key(STEP[(w[0] - x, w[1] - y)], 0.3)
                continue
            step = route(g, me, lambda a, b: (a, b) == w, blocked, goal_passable=False)
            if step is None:
                tried_wrecks.add(w)
        on_level = r.elapsed() - level_start
        if step is None and exit_at and on_level > descend_after:
            if me == exit_at:
                r.key(">", 0.5)
                continue
            step = route(g, me, lambda a, b: (a, b) == exit_at, blocked)
        if step is None:
            def frontier(a, b):
                if visits[(a, b)] > 1:
                    return False
                return any(0 <= a + dx < MAPH and 0 <= b + dy < MAPW
                           and cell(g, a + dx, b + dy) == " " for dx, dy in STEP)
            step = route(g, me, frontier, blocked)
        if step is None and exit_at:
            if me == exit_at:
                r.key(">", 0.5)
                continue
            step = route(g, me, lambda a, b: (a, b) == exit_at, blocked)
        if step is None:
            r.key(".", 0.15)
            continue
        play.aim = (x + step[0], y + step[1])
        r.key(STEP[step], 0.12)
    return "quit"


def take(args):
    """One recording; True when the robot lasted to the end."""
    soak = args.soak > 0
    r = rec.Rec("scrap", "Scrap", bindir=args.bindir,
                cast=os.path.join(r_tmp(), "soak.cast") if soak else None,
                extra_env={"ASAN_OPTIONS": "detect_leaks=0:log_path=" + os.path.join(r_tmp(), "asan")}
                if soak else None)
    r.wait_for("Welcome to Scrap", 8)
    r.pump(1.5)
    if soak:
        games = 0
        while r.elapsed() < args.soak:
            out = play(r, args.soak, 4)
            if out == "dead":
                games += 1
                r.key("y", 0.5)
                r.pump(0.5)
        print(f"soak: {games} games lost, level reached in the last: {level_of(r)}", file=sys.stderr)
        quit_game(r, 0.4)
        return True
    out = play(r, 50, 18)
    if out == "dead":
        r.pump(1.0)
        r.finish(b"n")
        return r.elapsed() > 45
    r.pump(1.0)
    quit_game(r, 1.2)
    return True


def quit_game(r, pause):
    """Clear any prompt, quit without saving, and answer no to another game."""
    for _ in range(40):
        msg = grid(r)[0]
        if "play again" in msg:
            break
        if "More" in msg[70:] or "Press any key" in msg:
            r.key(" ", 0.3)
        elif "Use +/-" in msg or "Invalid target" in msg or "which slot" in msg or "salvage" in msg:
            r.key("x", 0.3)
        elif "without saving" in msg:
            r.key("y", pause)
        else:
            r.key("Q", 0.6)
    r.pump(pause)
    r.finish(b"n")


def level_of(r):
    r.key("@", 0.3)
    m = re.search(r"level (\d+)", grid(r)[0])
    return m.group(1) if m else "?"


def r_tmp():
    d = os.environ.get("SCRAP_SOAK_DIR", "/tmp")
    os.makedirs(d, exist_ok=True)
    return d


ap = argparse.ArgumentParser()
ap.add_argument("--soak", type=float, default=0, help="play this many seconds, no preview")
ap.add_argument("--bindir", default=None, help="folder holding the scrap binary to run")
ap.add_argument("--debug", type=float, default=0, help="print the screen every this many seconds")
args = ap.parse_args()
DEBUG = args.debug
for attempt in range(6):
    if take(args):
        break
    print("the robot was destroyed early; recording again", file=sys.stderr)
