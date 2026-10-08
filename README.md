# Airlock

Something got loose on the station and the crew is hiding in the rooms. You
are the one left on their feet. Reach a worker, bring them down the corridor
to the shuttle, and go back for the next one. Your single button works the
nearest door, or arms an airlock when you stand under a hatch. An armed hatch
blows a few seconds later and sucks everything out of the connected corridor,
creatures and crew alike, so seal the bulkheads, check who is still out there,
and get behind a door yourself. Every worker you save breaches another room
and brings more creatures out of the vents. Atari 2600 looks, one screen,
inside your terminal.

<p align="center">
<img width="562" height="424" alt="airlock" src="https://github.com/user-attachments/assets/ff50ac67-a132-45ab-a641-4c57dbdad7fa" />
</p>

```bash
./play.sh
```

or `python3 -m airlock` from this folder. Add `--sound` for a terminal bell on
rescues, breaches and deaths. Needs Python 3 (ships with macOS) and a terminal
at least 80 columns by 22 rows. A 256-colour terminal gives the full palette;
8-colour terminals still work.

## Controls

| Key | Action |
| --- | --- |
| Arrows, WASD, HJKL | move |
| SPACE, ENTER, F, Z | the button: open or seal the door next to you, or arm the airlock above you |
| P | pause |
| ? | in-game briefing |
| M | toggle the terminal bell |
| Q, ESC | quit (asks first) |

Movement uses your OS key repeat, so hold a direction to keep walking.

## The station

The playfield is a 39x11 grid drawn in solid colour blocks, two terminal
columns per cell.

- **The corridor** runs along the top in navy, three cells tall. Two tan
  bulkhead doors split it into three segments. They start open.
- **The shuttle dock** is the light grey pad at the left end. Walk a following
  worker onto it and they are aboard. The dock has its own pressure door, so
  it is never vented and you are safe standing on it.
- **Six rooms** hang below the corridor in green, each behind a tan door in
  the wall. One worker (cyan) waits in each room. Rooms start sealed, which
  keeps the creatures out until you open them.
- **Three airlock hatches** sit in the hull above the corridor in orange, one
  per segment. Stand directly under one and press the button to arm it. It
  flashes red and yellow for about three and a half seconds, then blows.
- **Creatures** are the flickering green checkered things. They wander, and
  chase the nearest person within ten cells. They cannot open doors, and they
  cannot step onto the dock. Touching you costs a life; touching a worker
  kills the worker.

## Playing

1. Open a room door, step in, and touch the worker. They turn bright and
   follow one step behind you.
2. Walk them to the dock. They board the instant they step onto it, scoring
   100 times the shift number plus 50 for every worker already aboard.
3. Each rescue breaches a random safe room (it turns red, its door jams open
   and a vent starts producing creatures) and more creatures arrive. The
   creatures also get a little faster.
4. To clear a segment: seal the bulkheads around it, make sure no worker is in
   it, arm the hatch, then step into a room and seal the door behind you, or
   get past a bulkhead and seal that. Rooms whose doors are open vent too, so
   a jammed-open breached room goes with its segment.
5. When the hatch blows the whole region strobes and everything in it is
   pulled toward the hatch one cell at a time and lost. Creatures are 50
   points each. Workers caught out there are lost. If that includes you, so
   are you.

A shift ends when every worker is either aboard or gone. You get 200 points
per remaining life and the next shift starts with more creatures, rooms
already breached, faster arm timers and busier vents. You have three lives,
and respawn on the dock with two seconds of blinking invulnerability. The high
score is saved in `highscore.json` next to this file.

## Tips

- Seal the room door behind you when you go in for a worker. Creatures gather
  outside doors they want to get through, and that is exactly where you want
  them when the hatch blows.
- The left segment holds the dock. Keep its bulkhead sealed and it stays
  quiet; open it only to pass through.
- A following worker trails one cell behind you. If you duck into a room and
  seal the door at once, they are still in the corridor.
- Pressing the button again on an armed hatch disarms it.
- Doors will not close on anyone standing in them, including creatures. Lure
  them out of the doorway or vent them.
