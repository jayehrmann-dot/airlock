"""Entry point: python3 -m airlock [--sound]"""
import curses
import locale
import os
import sys
import time


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "-h" in argv or "--help" in argv:
        print("usage: python3 -m airlock [--sound]\n\n  --sound   ring the terminal bell on rescues, breaches and deaths")
        return 0
    sound = "--sound" in argv or "-s" in argv

    locale.setlocale(locale.LC_ALL, "")
    os.environ.setdefault("ESCDELAY", "25")
    if not os.environ.get("TERM"):
        os.environ["TERM"] = "xterm-256color"
    from .constants import TICK
    from .engine import Game, UP, DOWN, LEFT, RIGHT, FIRE, PAUSE, QUIT, HELP, BELL, ANY
    from .render import Renderer

    KEYMAP = {
        curses.KEY_UP: UP, ord("w"): UP, ord("W"): UP, ord("k"): UP,
        curses.KEY_DOWN: DOWN, ord("s"): DOWN, ord("S"): DOWN, ord("j"): DOWN,
        curses.KEY_LEFT: LEFT, ord("a"): LEFT, ord("A"): LEFT, ord("h"): LEFT,
        curses.KEY_RIGHT: RIGHT, ord("d"): RIGHT, ord("D"): RIGHT, ord("l"): RIGHT,
        ord(" "): FIRE, ord("\n"): FIRE, ord("\r"): FIRE, curses.KEY_ENTER: FIRE,
        ord("f"): FIRE, ord("F"): FIRE, ord("z"): FIRE, ord("Z"): FIRE,
        ord("p"): PAUSE, ord("P"): PAUSE,
        ord("q"): QUIT, ord("Q"): QUIT, 27: QUIT,
        ord("?"): HELP, ord("/"): HELP,
        ord("m"): BELL, ord("M"): BELL,
    }

    def run(stdscr):
        stdscr.nodelay(True)
        stdscr.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        g = Game(sound=sound)
        r = Renderer(stdscr)
        next_t = time.time()
        while g.running:
            acts = set()
            for _ in range(64):
                k = stdscr.getch()
                if k == -1:
                    break
                if k == curses.KEY_RESIZE:
                    continue
                acts.add(ANY)
                if k in (ord("y"), ord("Y")):
                    acts.add("yes")
                a = KEYMAP.get(k)
                if a is not None:
                    acts.add(a)
            g.update(acts)
            r.draw(g)
            if g.beep_pending:
                g.beep_pending = False
                try:
                    curses.beep()
                except curses.error:
                    pass
            next_t += TICK
            delay = next_t - time.time()
            if delay > 0:
                time.sleep(delay)
            else:
                next_t = time.time()
        return g.high

    try:
        high = curses.wrapper(run)
    except KeyboardInterrupt:
        high = None
    if high:
        print("Shuttle away. High score: %d." % high)
    else:
        print("Shuttle away.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
