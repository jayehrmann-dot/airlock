"""Constants, layout, tuning, palette and block font for Airlock."""

FPS = 20
TICK = 1.0 / FPS

# ---------------------------------------------------------------- station layout
# The station is a grid of GW x GH cells; each cell is two terminal columns
# wide and one row tall, which is roughly square in most terminal fonts.
GW, GH = 39, 11
ROW_SPACE = 0                  # stars above the hull
ROW_HULL = 1                   # outer hull with the airlock hatches
COR_TOP, COR_BOT = 2, 4        # the corridor, three cells tall
ROW_DOORS = 5                  # wall between corridor and rooms, holds room doors
ROOM_TOP, ROOM_BOT = 6, 9      # the rooms
ROW_BOTTOM = 10                # lower hull
DOCK_X0, DOCK_X1 = 1, 3        # the shuttle dock at the left end of the corridor
COR_X0, COR_X1 = 4, 37
ROOMS = [(4, 8), (10, 14), (16, 20), (22, 26), (28, 32), (34, 37)]   # x0..x1 inclusive
BULKHEADS = [15, 27]           # columns of the corridor bulkhead doors (3 tall)
HATCHES = [9, 21, 33]          # airlock hatch columns in the hull, one per segment
SPAWN_X = 36                   # where creatures crawl in when no room is breached
PLAYER_START = (2, 3)

# tile ids
SPACE, HULL, WALL, COR, ROOM, DOCK, DOOR, HATCH = range(8)
SAFE, BREACHED = 0, 1

# ---------------------------------------------------------------- screen layout
VIEW_COLS = GW * 2             # 78
HUD_ROWS = 2
PLAY_TOP = HUD_ROWS + 1
MSG_TOP = PLAY_TOP + GH + 1
MSG_ROWS = 3
VIEW_ROWS = MSG_TOP + MSG_ROWS   # 20 terminal rows
MIN_COLS, MIN_ROWS = 80, 22

# ---------------------------------------------------------------- rules
START_LIVES = 3
MOVE_COOLDOWN = 1              # ticks between player steps (10 cells/s at 20 fps)
FIRE_COOLDOWN = 6              # ticks before the button can be pressed again
ARM_DELAY_BASE = 70            # ticks between arming an airlock and the hatch blowing
ARM_DELAY_MIN = 40
VENT_PULL_EVERY = 2            # ticks between each pull step while venting
CREATURE_PERIOD_BASE = 9       # ticks between creature moves on shift 1
CREATURE_PERIOD_MIN = 3
CREATURE_CHASE_RANGE = 10
CREATURE_CHASE_PROB = 0.7
SPAWN_INTERVAL_BASE = 400      # ticks between vent spawns on shift 1 (20 s)
SPAWN_INTERVAL_MIN = 120
CREATURE_CAP_BASE = 8
INVULN_TICKS = 2 * FPS
DEAD_TICKS = 30
LEVEL_END_TICKS = 80
MSG_TICKS = 3 * FPS

SCORE_EVAC = 100               # times the shift number, plus 50 per worker already aboard
SCORE_EVAC_STEP = 50
SCORE_VENT = 50                # per creature blown into space
SCORE_LIFE_BONUS = 200         # per remaining life at the end of a shift

# ---------------------------------------------------------------- sprites
GLYPH_PLAYER = "▛▜"
GLYPH_WORKER = "▙▟"
GLYPH_CREATURE = ("▚▞", "▞▚")
GLYPH_DOOR_OPEN = "▏▕"
GLYPH_VENT = "▓▓"
GLYPH_SHUTTLE = (" ▄", "██", "▀ ")

# ---------------------------------------------------------------- palette
# name -> (256-colour index, basic 8-colour index)
# basic: 0 black 1 red 2 green 3 yellow 4 blue 5 magenta 6 cyan 7 white
PALETTE = {
    "bg":         (16, 0),
    "star":       (245, 7),
    "hull":       (25, 4),
    "wall":       (97, 5),
    "cor":        (17, 0),
    "room":       (22, 2),
    "room_bad":   (52, 1),
    "dock":       (250, 7),
    "shuttle":    (231, 7),
    "door":       (180, 3),
    "door_jam":   (196, 1),
    "hatch":      (166, 3),
    "arm1":       (196, 1),
    "arm2":       (226, 3),
    "strobe":     (252, 7),
    "player":     (214, 3),
    "worker":     (51, 6),
    "worker_f":   (123, 6),
    "creat1":     (46, 2),
    "creat2":     (34, 2),
    "vent1":      (196, 1),
    "vent2":      (124, 1),
    "text":       (214, 3),
    "text2":      (250, 7),
    "white":      (231, 7),
    "dim":        (240, 7),
    "good":       (46, 2),
    "bad":        (196, 1),
    "rb0":        (196, 1),
    "rb1":        (208, 3),
    "rb2":        (226, 3),
    "rb3":        (46, 2),
    "rb4":        (51, 6),
}

# 3x5 block font, 4 columns per glyph including the gap
FONT = {
    "A": [".█.", "█.█", "███", "█.█", "█.█"],
    "I": ["███", ".█.", ".█.", ".█.", "███"],
    "R": ["██.", "█.█", "██.", "█.█", "█.█"],
    "L": ["█..", "█..", "█..", "█..", "███"],
    "O": ["███", "█.█", "█.█", "█.█", "███"],
    "C": ["███", "█..", "█..", "█..", "███"],
    "K": ["█.█", "█.█", "██.", "█.█", "█.█"],
    "G": ["███", "█..", "█.█", "█.█", "███"],
    "M": ["█.█", "███", "█.█", "█.█", "█.█"],
    "E": ["███", "█..", "██.", "█..", "███"],
    "V": ["█.█", "█.█", "█.█", "█.█", ".█."],
    "S": ["███", "█..", "███", "..█", "███"],
    "H": ["█.█", "█.█", "███", "█.█", "█.█"],
    "F": ["███", "█..", "██.", "█..", "█.."],
    "T": ["███", ".█.", ".█.", ".█.", ".█."],
    "P": ["███", "█.█", "███", "█..", "█.."],
    "D": ["██.", "█.█", "█.█", "█.█", "██."],
    "N": ["█.█", "███", "███", "█.█", "█.█"],
    "U": ["█.█", "█.█", "█.█", "█.█", "███"],
    " ": ["...", "...", "...", "...", "..."],
}
