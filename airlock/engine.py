"""Game rules for Airlock. No curses in here so the logic can be tested headless."""
import json
import os
import random
from collections import deque

from .constants import *  # noqa: F401,F403

HIGH_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "highscore.json")

# abstract input actions, translated from keys by the front end
UP, DOWN, LEFT, RIGHT, FIRE, PAUSE, QUIT, HELP, BELL, ANY = range(10)
DIRS = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}


def vent_cell(room):
    x0, x1 = ROOMS[room]
    return ((x0 + x1) // 2, ROOM_BOT)


class Game:
    """All state lives here. Call update(actions) once per tick."""

    def __init__(self, sound=False):
        self.sound = sound
        self.beep_pending = False
        self.tick = 0
        self.mode = "title"
        self.prev_mode = "title"
        self.msg, self.msg_t = "", 0
        self.score, self.lives, self.level = 0, START_LIVES, 1
        self.high = self.load_high()
        self.new_high = False
        self.running = True
        self.build_map()
        self.workers, self.creatures = [], []
        self.evac = self.lost = self.total = 0
        self.player = {"x": PLAYER_START[0], "y": PLAYER_START[1]}
        self.vent = None
        self.vent_kills = 0
        self.inv = 0
        self.t = 0
        self.hatch = {hx: {"state": "closed", "t": 0} for hx in HATCHES}

    # ------------------------------------------------------------ persistence
    def load_high(self):
        try:
            with open(HIGH_PATH) as f:
                return int(json.load(f).get("high", 0))
        except (OSError, ValueError):
            return 0

    def save_high(self):
        try:
            with open(HIGH_PATH, "w") as f:
                json.dump({"high": self.high}, f)
        except OSError:
            pass

    # ------------------------------------------------------------ helpers
    def say(self, text, ticks=MSG_TICKS):
        self.msg, self.msg_t = text, ticks

    def beep(self):
        if self.sound:
            self.beep_pending = True

    def tile(self, x, y):
        if 0 <= x < GW and 0 <= y < GH:
            return self.tiles[y][x]
        return SPACE

    def is_open_door(self, x, y):
        gid = self.cell_door.get((x, y))
        return gid is not None and self.door_open[gid]

    def walkable(self, x, y, creature=False):
        t = self.tile(x, y)
        if t in (COR, ROOM):
            return True
        if t == DOCK:
            return not creature
        if t == DOOR:
            return self.is_open_door(x, y)
        return False

    def room_at(self, x, y):
        if ROOM_TOP <= y <= ROOM_BOT:
            for i, (x0, x1) in enumerate(ROOMS):
                if x0 <= x <= x1:
                    return i
        return None

    def creature_at(self, x, y):
        for c in self.creatures:
            if c["x"] == x and c["y"] == y:
                return c
        return None

    def worker_at(self, x, y):
        for w in self.workers:
            if w["x"] == x and w["y"] == y:
                return w
        return None

    def following(self):
        for w in self.workers:
            if w["follow"]:
                return w
        return None

    def in_vent(self, x, y):
        return self.vent is not None and (x, y) in self.vent["dist"]

    # ------------------------------------------------------------ station
    def build_map(self):
        t = [[SPACE] * GW for _ in range(GH)]
        for x in range(GW):
            t[ROW_HULL][x] = HULL
            t[ROW_BOTTOM][x] = HULL
        for y in range(ROW_HULL, ROW_BOTTOM + 1):
            t[y][0] = HULL
            t[y][GW - 1] = HULL
        for y in range(COR_TOP, COR_BOT + 1):
            for x in range(DOCK_X0, DOCK_X1 + 1):
                t[y][x] = DOCK
            for x in range(COR_X0, COR_X1 + 1):
                t[y][x] = COR
        for y in range(ROW_DOORS, ROOM_BOT + 1):
            for x in range(COR_X0, COR_X1 + 1):
                t[y][x] = WALL
        for x0, x1 in ROOMS:
            for y in range(ROOM_TOP, ROOM_BOT + 1):
                for x in range(x0, x1 + 1):
                    t[y][x] = ROOM
        # doors: group id -> cells; room doors are gids 0..5, bulkheads follow
        self.door_cells, self.door_open, self.cell_door, self.jammed = {}, {}, {}, set()
        for i, (x0, x1) in enumerate(ROOMS):
            dx = (x0 + x1) // 2
            t[ROW_DOORS][dx] = DOOR
            self.door_cells[i] = [(dx, ROW_DOORS)]
            self.door_open[i] = False
            self.cell_door[(dx, ROW_DOORS)] = i
        for j, bx in enumerate(BULKHEADS):
            gid = len(ROOMS) + j
            cells = [(bx, y) for y in range(COR_TOP, COR_BOT + 1)]
            for c in cells:
                t[c[1]][c[0]] = DOOR
                self.cell_door[c] = gid
            self.door_cells[gid] = cells
            self.door_open[gid] = True
        for hx in HATCHES:
            t[ROW_HULL][hx] = HATCH
        self.tiles = t
        self.room_state = [SAFE] * len(ROOMS)

    def new_level(self):
        self.build_map()
        self.workers = []
        for x0, x1 in ROOMS:
            self.workers.append({"x": random.randint(x0, x1),
                                 "y": random.randint(ROOM_TOP, ROOM_BOT - 1),
                                 "follow": False})
        self.creatures = []
        self.evac, self.lost, self.total = 0, 0, len(self.workers)
        self.player = {"x": PLAYER_START[0], "y": PLAYER_START[1]}
        self.move_cd = self.fire_cd = 0
        self.vent, self.vent_kills = None, 0
        self.inv = 0
        self.hatch = {hx: {"state": "closed", "t": 0} for hx in HATCHES}
        lv = self.level - 1
        self.arm_delay = max(ARM_DELAY_MIN, ARM_DELAY_BASE - 10 * lv)
        self.spawn_interval = max(SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_BASE - 40 * lv)
        self.spawn_t = self.spawn_interval
        self.cap = CREATURE_CAP_BASE + 2 * self.level
        self.retune()
        for _ in range(1 + self.level):
            self.spawn_creature(SPAWN_X, random.randint(COR_TOP, COR_BOT))
        for _ in range(min(lv, 3)):
            self.breach_random(quiet=True)
        self.mode = "play"
        self.say("SHIFT %d: EVACUATE %d WORKERS" % (self.level, self.total))

    def retune(self):
        self.creature_period = max(CREATURE_PERIOD_MIN,
                                   CREATURE_PERIOD_BASE - (self.level - 1) - self.evac // 2)

    # ------------------------------------------------------------ flow
    def start_new(self):
        self.score, self.lives, self.level = 0, START_LIVES, 1
        self.new_high = False
        self.new_level()

    def end_level(self):
        bonus = SCORE_LIFE_BONUS * self.lives
        self.score += bonus
        self.mode, self.t = "levelend", LEVEL_END_TICKS
        self.say("SHIFT %d COMPLETE  BONUS %d" % (self.level, bonus))
        self.beep()

    def game_over(self):
        self.mode = "gameover"
        if self.score > self.high:
            self.high, self.new_high = self.score, True
            self.save_high()
        self.say("GAME OVER")

    def respawn(self):
        self.player = {"x": PLAYER_START[0], "y": PLAYER_START[1]}
        self.inv = INVULN_TICKS
        self.move_cd = self.fire_cd = 0
        self.mode = "play"

    # ------------------------------------------------------------ spawning
    def spawn_creature(self, x, y):
        if len(self.creatures) >= self.cap:
            return False
        for nx, ny in ((x, y), (x + 1, y), (x - 1, y), (x, y - 1), (x, y + 1), (x + 2, y), (x - 2, y)):
            if self.walkable(nx, ny, creature=True) and not self.creature_at(nx, ny):
                self.creatures.append({"x": nx, "y": ny})
                return True
        return False

    def spawn_from_breach(self):
        bad = [i for i, s in enumerate(self.room_state) if s == BREACHED]
        if bad:
            return self.spawn_creature(*vent_cell(random.choice(bad)))
        return self.spawn_creature(SPAWN_X, random.randint(COR_TOP, COR_BOT))

    def breach_random(self, quiet=False):
        safe = [i for i, s in enumerate(self.room_state) if s == SAFE]
        if not safe:
            return
        r = random.choice(safe)
        self.room_state[r] = BREACHED
        self.door_open[r] = True
        self.jammed.add(r)
        self.spawn_creature(*vent_cell(r))
        if not quiet:
            self.say("HULL BREACH IN ROOM %d! DOOR JAMMED OPEN" % (r + 1))
            self.beep()

    def escalate(self):
        self.breach_random()
        for _ in range(1 + self.level // 2):
            self.spawn_from_breach()
        self.retune()

    # ------------------------------------------------------------ player
    def pickup(self, w):
        w["follow"] = True
        self.say("WORKER FOLLOWING. GET THEM TO THE SHUTTLE")

    def move_player(self, dx, dy):
        p = self.player
        nx, ny = p["x"] + dx, p["y"] + dy
        if not self.walkable(nx, ny):
            return
        w = self.worker_at(nx, ny)
        if w:
            if not w["follow"] and not self.following():
                self.pickup(w)
            return
        ox, oy = p["x"], p["y"]
        p["x"], p["y"] = nx, ny
        f = self.following()
        if f and (f["x"], f["y"]) != (ox, oy):
            f["x"], f["y"] = ox, oy
        if not f:
            for w in self.workers:
                if not w["follow"] and abs(w["x"] - nx) + abs(w["y"] - ny) == 1:
                    self.pickup(w)
                    break
        self.check_collisions()
        self.check_delivery()

    def button(self):
        px, py = self.player["x"], self.player["y"]
        gids = set()
        for nx, ny in ((px, py), (px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
            gid = self.cell_door.get((nx, ny))
            if gid is not None:
                gids.add(gid)
        if gids:
            gid = min(gids)
            if gid in self.jammed:
                self.say("DOOR JAMMED")
                return
            if self.door_open[gid]:
                for c in self.door_cells[gid]:
                    if c == (px, py) or self.creature_at(*c) or self.worker_at(*c):
                        self.say("DOORWAY BLOCKED")
                        return
                self.door_open[gid] = False
                self.say("DOOR SEALED")
            else:
                self.door_open[gid] = True
                self.say("DOOR OPEN")
            return
        if py == COR_TOP and px in self.hatch:
            h = self.hatch[px]
            if h["state"] == "closed":
                if any(o["state"] != "closed" for o in self.hatch.values()):
                    self.say("AIRLOCK CYCLING")
                    return
                h["state"], h["t"] = "armed", self.arm_delay
                self.say("AIRLOCK ARMED! CLEAR THE CORRIDOR AND SEAL A DOOR")
                self.beep()
            elif h["state"] == "armed":
                h["state"] = "closed"
                self.say("AIRLOCK DISARMED")
            return
        self.say("NOTHING TO OPERATE HERE")

    def check_delivery(self):
        f = self.following()
        if f and self.tile(f["x"], f["y"]) == DOCK:
            self.workers.remove(f)
            self.evac += 1
            pts = SCORE_EVAC * self.level + SCORE_EVAC_STEP * (self.evac - 1)
            self.score += pts
            self.say("WORKER ABOARD! +%d" % pts)
            self.beep()
            self.escalate()

    # ------------------------------------------------------------ deaths
    def player_die(self, why):
        f = self.following()
        if f:
            f["follow"] = False
        self.mode, self.t = "dying", DEAD_TICKS
        self.say(why)
        self.beep()

    def worker_die(self, w, why):
        if w in self.workers:
            self.workers.remove(w)
        self.lost += 1
        self.say(why)
        self.beep()

    def check_collisions(self):
        p = self.player
        for w in list(self.workers):
            if self.creature_at(w["x"], w["y"]):
                self.worker_die(w, "WORKER LOST!")
        if self.mode == "play" and self.inv == 0 and self.creature_at(p["x"], p["y"]):
            self.player_die("THE CREATURE GOT YOU!")

    # ------------------------------------------------------------ creatures
    def move_creatures(self):
        targets = [(self.player["x"], self.player["y"])] + [(w["x"], w["y"]) for w in self.workers]
        for c in self.creatures:
            if self.in_vent(c["x"], c["y"]):
                continue
            opts = [(c["x"] + dx, c["y"] + dy) for dx, dy in DIRS.values()]
            opts = [o for o in opts if self.walkable(*o, creature=True) and not self.creature_at(*o)]
            if not opts:
                continue
            tx, ty = min(targets, key=lambda t: abs(t[0] - c["x"]) + abs(t[1] - c["y"]))
            if abs(tx - c["x"]) + abs(ty - c["y"]) <= CREATURE_CHASE_RANGE and random.random() < CREATURE_CHASE_PROB:
                best = min(abs(o[0] - tx) + abs(o[1] - ty) for o in opts)
                opts = [o for o in opts if abs(o[0] - tx) + abs(o[1] - ty) == best]
            c["x"], c["y"] = random.choice(opts)
        self.check_collisions()

    # ------------------------------------------------------------ airlocks
    def vent_region(self, hx):
        """Cells that lose their air when hatch hx opens: everything reachable
        from the hatch through corridor, rooms and open doors. The shuttle
        dock has its own pressure door and is never part of it."""
        start = (hx, COR_TOP)
        dist = {start: 0}
        q = deque([start])
        while q:
            x, y = q.popleft()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) in dist:
                    continue
                t = self.tile(nx, ny)
                if t in (COR, ROOM) or (t == DOOR and self.is_open_door(nx, ny)):
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    q.append((nx, ny))
        return dist

    def open_hatch(self, hx):
        dist = self.vent_region(hx)
        self.vent = {"hx": hx, "dist": dist}
        self.vent_kills = 0
        h = self.hatch[hx]
        h["state"] = "open"
        h["t"] = VENT_PULL_EVERY * (max(dist.values()) + 2) + 6
        self.say("DECOMPRESSION!")
        self.beep()

    def pull_step(self):
        dist = self.vent["dist"]

        def pull(e):
            d = dist[(e["x"], e["y"])]
            if d == 0:
                return True
            for nx, ny in ((e["x"] + 1, e["y"]), (e["x"] - 1, e["y"]), (e["x"], e["y"] + 1), (e["x"], e["y"] - 1)):
                if dist.get((nx, ny)) == d - 1:
                    e["x"], e["y"] = nx, ny
                    return False
            return True

        for c in list(self.creatures):
            if (c["x"], c["y"]) in dist and pull(c):
                self.creatures.remove(c)
                self.vent_kills += 1
                self.score += SCORE_VENT
        for w in list(self.workers):
            if (w["x"], w["y"]) in dist and pull(w):
                w["follow"] = False
                self.worker_die(w, "WORKER BLOWN INTO SPACE!")
        p = self.player
        if self.mode == "play" and (p["x"], p["y"]) in dist and pull(p):
            self.player_die("YOU WERE BLOWN INTO SPACE!")

    def update_hatches(self):
        for hx, h in self.hatch.items():
            if h["state"] == "armed":
                h["t"] -= 1
                if h["t"] <= 0:
                    self.open_hatch(hx)
            elif h["state"] == "open":
                h["t"] -= 1
                if h["t"] <= 0:
                    h["state"] = "closed"
                    self.vent = None
                    self.say("AIRLOCK SEALED. %d CREATURE%s VENTED" % (self.vent_kills, "" if self.vent_kills == 1 else "S"))
        if self.vent and self.tick % VENT_PULL_EVERY == 0:
            self.pull_step()

    # ------------------------------------------------------------ main update
    def update(self, acts):
        self.tick += 1
        if self.msg_t > 0:
            self.msg_t -= 1
        if QUIT in acts and self.mode in ("title", "gameover"):
            self.running = False
            return
        if BELL in acts:
            self.sound = not self.sound
            self.say("SOUND %s" % ("ON" if self.sound else "OFF"), FPS)
        m = self.mode
        if m == "title":
            if HELP in acts:
                self.prev_mode, self.mode = "title", "help"
            elif FIRE in acts:
                self.start_new()
        elif m == "help":
            if ANY in acts:
                self.mode = self.prev_mode
        elif m == "pause":
            if PAUSE in acts or FIRE in acts:
                self.mode = "play"
            elif HELP in acts:
                self.prev_mode, self.mode = "pause", "help"
            elif QUIT in acts:
                self.prev_mode, self.mode = "pause", "quit"
        elif m == "quit":
            if "yes" in acts:
                self.mode = "title"
                if self.score > self.high:
                    self.high, self.new_high = self.score, True
                    self.save_high()
            elif ANY in acts:
                self.mode = self.prev_mode
        elif m == "play":
            if PAUSE in acts:
                self.mode = "pause"
            elif HELP in acts:
                self.prev_mode, self.mode = "pause", "help"
            elif QUIT in acts:
                self.prev_mode, self.mode = "play", "quit"
            else:
                self.tick_play(acts)
        elif m == "dying":
            self.t -= 1
            if self.t <= 0:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over()
                else:
                    self.respawn()
        elif m == "levelend":
            self.t -= 1
            if self.t <= 0:
                self.level += 1
                self.new_level()
        elif m == "gameover":
            if FIRE in acts:
                self.start_new()

    def tick_play(self, acts):
        p = self.player
        if self.inv > 0:
            self.inv -= 1
        stuck = self.in_vent(p["x"], p["y"])
        if self.move_cd > 0:
            self.move_cd -= 1
        elif not stuck:
            for a in (UP, DOWN, LEFT, RIGHT):
                if a in acts:
                    self.move_player(*DIRS[a])
                    self.move_cd = MOVE_COOLDOWN
                    break
        if self.fire_cd > 0:
            self.fire_cd -= 1
        elif FIRE in acts and not stuck:
            self.button()
            self.fire_cd = FIRE_COOLDOWN
        if self.mode != "play":
            return
        if self.tick % self.creature_period == 0:
            self.move_creatures()
        if self.mode != "play":
            return
        self.update_hatches()
        if self.mode != "play":
            return
        self.spawn_t -= 1
        if self.spawn_t <= 0:
            self.spawn_t = self.spawn_interval
            if any(s == BREACHED for s in self.room_state) and self.spawn_from_breach():
                self.say("SOMETHING CRAWLED OUT OF A VENT", FPS)
        if not self.workers and self.vent is None and all(h["state"] == "closed" for h in self.hatch.values()):
            self.end_level()
