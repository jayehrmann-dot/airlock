"""Curses drawing for Airlock: solid colour blocks, two columns per cell, 2600 style."""
import curses

from .constants import *  # noqa: F401,F403
from .engine import vent_cell

HELP_LINES = [
    "THE STATION IS INFESTED. GET THE WORKERS TO THE SHUTTLE, ONE AT A TIME.",
    "",
    "MOVE WITH THE ARROWS OR WASD. SPACE IS YOUR ONE BUTTON.",
    "STAND NEXT TO A DOOR AND PRESS IT TO OPEN OR SEAL THAT DOOR.",
    "STAND UNDER A HATCH IN THE TOP HULL AND PRESS IT TO ARM THE AIRLOCK.",
    "",
    "TOUCH A WORKER AND THEY FOLLOW YOU. WALK THEM ONTO THE SHUTTLE DOCK.",
    "AN ARMED AIRLOCK BLOWS AFTER A FEW SECONDS AND SUCKS OUT EVERYTHING",
    "IN THE CONNECTED CORRIDOR, ROOMS WITH OPEN DOORS INCLUDED.",
    "SEAL THE BULKHEADS TO TRAP THE CREATURES, THEN GET BEHIND A SEALED DOOR.",
    "THE SHUTTLE DOCK IS SAFE. ANYONE ELSE LEFT IN THE CORRIDOR IS LOST.",
    "",
    "CREATURES CANNOT OPEN DOORS. EVERY EVACUATION BREACHES ANOTHER ROOM,",
    "JAMS ITS DOOR OPEN AND BRINGS MORE CREATURES OUT OF THE VENTS.",
]

TITLE_LINES = [
    "AN ATARI 2600 STYLE STATION EVACUATION",
    "",
    "ESCORT WORKERS TO THE SHUTTLE ONE AT A TIME.",
    "YOUR BUTTON WORKS THE DOORS AND THE AIRLOCKS.",
    "BLOW THE CREATURES INTO SPACE, BUT CHECK THE CORRIDOR FIRST.",
    "EVERY EVACUATION BRINGS MORE CREATURES AND FEWER SAFE ROOMS.",
]


class Renderer:
    def __init__(self, stdscr):
        self.scr = stdscr
        self.pairs = {}
        self.colors_ok = curses.has_colors()
        if self.colors_ok:
            curses.start_color()
            try:
                curses.use_default_colors()
            except curses.error:
                pass
        self.many = self.colors_ok and curses.COLORS >= 256
        self.max_pairs = curses.COLOR_PAIRS if self.colors_ok else 0
        self.oy = self.ox = 0

    # ------------------------------------------------------------ colours
    def cidx(self, name):
        full, basic = PALETTE[name]
        return full if self.many else basic

    def attr(self, fg, bg="bg", bold=False):
        if not self.colors_ok:
            return curses.A_BOLD if bold else 0
        key = (self.cidx(fg), self.cidx(bg))
        if key not in self.pairs:
            n = len(self.pairs) + 1
            if n >= self.max_pairs:
                return 0
            try:
                curses.init_pair(n, key[0], key[1])
            except curses.error:
                return 0
            self.pairs[key] = n
        a = curses.color_pair(self.pairs[key])
        return a | curses.A_BOLD if bold else a

    # ------------------------------------------------------------ primitives
    def put(self, y, x, s, attr=0):
        try:
            self.scr.addstr(y, x, s, attr)
        except curses.error:
            pass

    def fill(self, y0, x0, rows, cols, attr):
        for y in range(y0, y0 + rows):
            self.put(y, x0, " " * cols, attr)

    def center(self, y, text, attr=0):
        self.put(y, self.ox + (VIEW_COLS - len(text)) // 2, text, attr)

    def big(self, y, x, text, attr):
        """Block font, two columns per pixel. attr may be a function of the row."""
        for i, ch in enumerate(text.upper()):
            glyph = FONT.get(ch, FONT[" "])
            for r, row in enumerate(glyph):
                a = attr(r) if callable(attr) else attr
                for c, px in enumerate(row):
                    if px == "█":
                        self.put(y + r, x + (i * 4 + c) * 2, "██", a)

    def big_center(self, y, text, attr):
        w = (len(text) * 4 - 1) * 2
        self.big(y, self.ox + (VIEW_COLS - w) // 2, text, attr)

    def rainbow(self, g, phase=0):
        names = ["rb0", "rb1", "rb2", "rb3", "rb4"]

        def pick(r):
            return self.attr(names[(r + phase + g.tick // 4) % len(names)])
        return pick

    # ------------------------------------------------------------ field
    def cell(self, x, y, glyph, fg, bg):
        self.put(self.oy + PLAY_TOP + y, self.ox + 2 * x, glyph, self.attr(fg, bg))

    def base_cell(self, g, x, y):
        """Glyph and colours for the station under any entity at (x, y)."""
        t = g.tiles[y][x]
        f = g.tick
        glyph, fg, bg = "  ", "white", "bg"
        if t == SPACE:
            if (x * 7 + 3) % 5 == 0:
                glyph, fg = " .", "star"
        elif t == HULL:
            bg = "hull"
        elif t == WALL:
            bg = "wall"
        elif t == COR:
            bg = "cor"
        elif t == DOCK:
            bg = "dock"
            r = y - COR_TOP
            if x == DOCK_X0:
                glyph, fg = GLYPH_SHUTTLE[r], "shuttle"
        elif t == ROOM:
            r = g.room_at(x, y)
            if g.room_state[r] == BREACHED:
                bg = "room_bad"
                if (x, y) == vent_cell(r):
                    glyph, fg = GLYPH_VENT, ("vent1" if f % 4 < 2 else "vent2")
            else:
                bg = "room"
        elif t == DOOR:
            gid = g.cell_door[(x, y)]
            if g.door_open[gid]:
                bg, glyph = "cor", GLYPH_DOOR_OPEN
                fg = "door_jam" if gid in g.jammed else "door"
            else:
                bg = "door"
        elif t == HATCH:
            h = g.hatch[x]
            if h["state"] == "closed":
                bg = "hatch"
            elif h["state"] == "armed":
                bg = "arm1" if (f // 3) % 2 == 0 else "arm2"
            else:
                bg = "bg"
        if g.in_vent(x, y) and f % 2 == 0:
            bg = "strobe"
        return glyph, fg, bg

    def draw_field(self, g):
        for y in range(GH):
            for x in range(GW):
                glyph, fg, bg = self.base_cell(g, x, y)
                self.cell(x, y, glyph, fg, bg)
        for w in g.workers:
            _, _, bg = self.base_cell(g, w["x"], w["y"])
            fg = "worker_f" if w["follow"] else "worker"
            if w["follow"] and g.tick % 8 < 2:
                fg = "white"
            self.cell(w["x"], w["y"], GLYPH_WORKER, fg, bg)
        for c in g.creatures:
            _, _, bg = self.base_cell(g, c["x"], c["y"])
            k = g.tick % 2
            self.cell(c["x"], c["y"], GLYPH_CREATURE[k], "creat1" if k == 0 else "creat2", bg)
        p = g.player
        if g.mode == "gameover":
            return
        if g.inv > 0 and g.tick % 4 < 2 and g.mode == "play":
            return
        _, _, bg = self.base_cell(g, p["x"], p["y"])
        fg = "player"
        if g.mode == "dying":
            fg = "white" if g.tick % 2 == 0 else "bad"
        self.cell(p["x"], p["y"], GLYPH_PLAYER, fg, bg)

    # ------------------------------------------------------------ hud and text
    def draw_hud(self, g):
        y = self.oy
        tx = self.attr("text", bold=True)
        t2 = self.attr("text2")
        self.put(y, self.ox, "SCORE %06d" % g.score, tx)
        self.center(y, "SHIFT %d" % g.level, tx)
        s = "HI %06d" % g.high
        self.put(y, self.ox + VIEW_COLS - len(s), s, t2)
        self.put(y + 1, self.ox, "ABOARD %d/%d" % (g.evac, g.total), self.attr("good"))
        self.center(y + 1, "LOST %d" % g.lost, self.attr("bad" if g.lost else "dim"))
        x = self.ox + VIEW_COLS - 3 * START_LIVES
        for i in range(START_LIVES):
            on = i < g.lives
            self.put(y + 1, x + 3 * i, GLYPH_PLAYER, self.attr("player" if on else "dim"))

    def draw_messages(self, g):
        y = self.oy + MSG_TOP
        if g.msg_t > 0 and g.msg:
            self.center(y, g.msg, self.attr("text", bold=True))
        x = self.ox + 1
        legend = [(GLYPH_PLAYER, "player", "YOU"), (GLYPH_WORKER, "worker", "WORKER"),
                  (GLYPH_CREATURE[0], "creat1", "CREATURE"), ("██", "door", "DOOR"),
                  ("██", "hatch", "AIRLOCK"), ("██", "dock", "SHUTTLE")]
        for glyph, col, label in legend:
            self.put(y + 1, x, glyph, self.attr(col))
            self.put(y + 1, x + 3, label, self.attr("text2"))
            x += 3 + len(label) + 3
        self.center(y + 2, "ARROWS/WASD MOVE   SPACE BUTTON   P PAUSE   ? HELP   M SOUND   Q QUIT",
                    self.attr("dim"))

    def overlay(self, lines, color="text"):
        rows = len(lines) + 2
        y0 = self.oy + PLAY_TOP + COR_TOP - 1
        self.fill(y0, self.ox + 14, rows, VIEW_COLS - 28, self.attr("white", "bg"))
        for i, line in enumerate(lines):
            self.center(y0 + 1 + i, line, self.attr(color, bold=True))

    def draw_title(self, g):
        y = self.oy
        self.big_center(y + 1, "AIRLOCK", self.rainbow(g))
        for i, line in enumerate(TITLE_LINES):
            self.center(y + 8 + i, line, self.attr("text2" if i else "text", bold=(i == 0)))
        if g.tick % 20 < 14:
            self.center(y + 15, "PRESS SPACE TO START", self.attr("white", bold=True))
        self.center(y + 17, "? FOR THE BRIEFING    Q TO QUIT", self.attr("dim"))
        self.center(y + 19, "HIGH SCORE %06d" % g.high, self.attr("text"))

    def draw_help(self, g):
        y = self.oy
        self.center(y, "BRIEFING", self.attr("text", bold=True))
        for i, line in enumerate(HELP_LINES):
            self.center(y + 2 + i, line, self.attr("text2"))
        self.center(y + 3 + len(HELP_LINES), "PRESS ANY KEY", self.attr("white", bold=True))

    def too_small(self, rows, cols):
        self.put(0, 0, "AIRLOCK needs a terminal of at least %dx%d (this one is %dx%d)."
                 % (MIN_COLS, MIN_ROWS, cols, rows))
        self.put(1, 0, "Enlarge the window, or press Q to quit.")

    # ------------------------------------------------------------ frame
    def draw(self, g):
        self.scr.erase()
        rows, cols = self.scr.getmaxyx()
        if rows < MIN_ROWS or cols < MIN_COLS:
            self.too_small(rows, cols)
            self.scr.refresh()
            return
        self.oy = max(0, (rows - VIEW_ROWS) // 2)
        self.ox = max(0, (cols - VIEW_COLS) // 2)
        if g.mode == "title":
            self.draw_title(g)
        elif g.mode == "help":
            self.draw_help(g)
        else:
            self.draw_hud(g)
            self.draw_field(g)
            self.draw_messages(g)
            if g.mode == "pause":
                self.overlay(["PAUSED", "SPACE OR P TO RESUME"])
            elif g.mode == "quit":
                self.overlay(["ABANDON THE STATION?", "Y TO QUIT, ANY OTHER KEY TO STAY"], "bad")
            elif g.mode == "gameover":
                lines = ["GAME OVER", "SCORE %06d" % g.score, "PRESS SPACE TO PLAY AGAIN, Q FOR TITLE"]
                if g.new_high:
                    lines.insert(1, "NEW HIGH SCORE!")
                self.overlay(lines)
            elif g.mode == "levelend":
                self.overlay(["SHIFT %d COMPLETE" % g.level,
                              "ABOARD %d   LOST %d   BONUS %d" % (g.evac, g.lost, SCORE_LIFE_BONUS * g.lives)], "good")
        self.scr.refresh()
