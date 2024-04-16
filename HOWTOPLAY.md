How to Play
===========

The game simulates a 2D version of spaceborne warfare on an interstellar scale,
similarly to Star Trek and other sci-fi. You are the commander of a squadron of
armed starships, tasked with achieving an objective based on the chosen
scenario.

In the demo scenario, `waves-of-raiders.py`, you must protect local spaceborne
colonies from increasing waves of hostile raiders.

User Interface
--------------

The user interface is a simple monochrome command-line. It has a few game
management commands:

* `help`, also spelt `?`, gives in-line help.
* `quit`, also triggered with an EOF character, quits the program.
* `debug` drops into a pdb debug session.
* `r N` runs the simulation for N ticks, defaulting to 24. See Not Turn-Based below.

Other commands are for gameplay itself. For these, ships and other vessels are
identified by a short unique label, which are used in information displays and
in the commands you enter. Each label is a two-character code such as `e5`:

* The first character is the unit type:
  * `s` for a ship in your squadron that you control
  * `e` for an enemy ship
  * `c` for a stationary colony
  * `:` signifies a grid point with more than one unit; a footnote lists its contents.
* The second character is a unique number or letter assigned by the UI.

So, if the scenario has four enemies, they will be labelled e0, e1, e2, and e3.

These commands let you view information about vessels and their positions:

* `sm` shows the strategic map, which is the entire field of play and the
  region of space you're responsible for protecting.
* `map X Y [RADIUS=8] [SCALE=1.0]` shows a map with custom centering and scale.
* `ls [VESSEL...]` lists spaceborne objects, providing one line of information
  for each. List all objects with `ls` by itself.
* `sh` is like `ls` but shows more details.

These commands issue orders:

* `at SHIP... TARGET` Attack. Ships will pursue a target, intercept it, and
  engage in combat. It will continue pursuit as needed until the target is
  destroyed.
* `mv SHIP... X Y` Move to the given coordinates.
* `vs SHIP... TARGET` Visit the given vessel by traveling to its coordinates.
  Note that if the target is in motion, it won't be pursued nor followed.
* `wt SHIP...` Hold position until ordered to do otherwise.

Not Turn-Based, Not Real-Time, but Event-Based
----------------------------------------------

The simulation starts out paused. Any time the simulation is paused, you can
use the command line to examine the strategic situation, and issue orders to
your ships, including repeatedly replacing existing orders with new ones.

Once all your ships have orders, you can start the simulation running with `r`.
It will simulate 24 hours of in-game time then pause again. Use eg `r 16` to
run for 16 hours instead. You can't pause the simulation while it's running,
but it will decide to pause on its own if anything important happens, such as:

* Combat has occurred.
* A ship has no orders, most likely because it completed its current orders. (If
  you need a ship to remain stationary, order it to wait with `wt`.)
* The scenario's victory or defeat conditions have been met. You are returned
  to the command line so you can examine the final simulation state.

In this way, the decision-free parts of the simulation can be computed
instantly, but you'll be free to make unhurried command decisions when needed.

This timing system, which I call 'event-based,' was needed to avoid painful
design compromises. Mostly games are implemented monotonically. In turn-based
games, for instance, each turn represents an equal time interval. But in naval
warfare, upon which starship combat is generally based, long periods of time
pass without any meaningful strategic decisions. So a conventional design would
result in significant 'dead' play time.

Event-based timing instead lets players run large or small blocks of simulation
time as they wish, say `r 5` or `r 25` as needed, yet be safe from unpleasant
surprises thanks to the game's event-based pausing.

Simulation Fundamentals
-----------------------

The simulation runs at 1 tick = 1 simulated hour. Each tick has several
internal steps. In simplified form:

1. Movement: Each unit moves a short distance based on its speed and orders.
2. Combat: Any colocated enemies automatically engage in combat.
3. Post-action steps, such as:
    * Non-player-controlled units are given new orders if needed.
    * If a vessel didn't fight this tick, shields recharge and repairs are performed.

Objects' positions in space are given by a pair of floating point values, (X,
Y), oriented as in algebra class. Distances are in light years. At the scale of
light years, vessels can't encounter each other, as allies nor enemies, unless
their coordinates are very nearly equal. Likewise sublight travel is irrelevant
at this scale, so it is not implemented. Per cinematic convention, superluminal
travel is in straight lines, with instantaneous acceleration.

To view the entire strategic map use `sm`. Use `map` to zoom in on smaller
areas. To view the coordinates of an object, rounded off to hundredths of a
light year, use `ls` or `sh`. Such output is highly approximate, useful for
reasoning spatially but not precisely. Two vessels could appear to have equal
positions but still be separated by billions of miles. "Space is big," and
light years are enormous.

For moving your ships around in space, use `mv`, `at`, and `vs`. Be careful
when constructing a `mv` command from coordinates copied from `ls` or `sh`, or
eyeballed from a map, due to the approximations discussed above.

Vessels
-------
Vessels include both friendly ships, enemy ships, and stationary facilities
such as space colonies. A comprehensive display of any vessel is given by `sh`;
`ls` lists the first line alone for brevity:

```
0h> sh s0
s0 Defender-1 (22.00, 60.00) W=1.00 CV=1.00 [###])))  MOVING to (25.00, 32.00)
    Base Repair Rate: 1% / hour        Morale: 0.00
    SYSTEM STATUS
        shields:  100%
        tactical: 100%
        drive:    100%
```

* `s1` is the vessel's label, shown on maps and used on the command-line.
* `Defender-1` is the vessel's in-game name, what the crew would call it.
* `(22.00, 60.00)` is the unit's position rounded to two decimale places.
* `W=1.00` is warp speed in light years per hour (1 hour = 1 simulation tick).
* `CV=1.00` is the unit's combat value; higher is better. See Combat below.
* `[###])))` is the unit's damage display:
  * `)))` indicates full shields.
  * `###` similarly means its hull has suffered little or no damage.
  * Fewer characters indicate more damage.
  * `[   ]   ` indicates the vessel is nearly destroyed.
* `MOVING to (25.00, 32.00)` is the ship's current orders.
* `Morale: 0.00`: This vessel has neutral morale; see Morale below.
* `Base Repair Rate: 1% / hour`: Each hour away from combat, this ship's crew
  repairs 1% of its system damage. See Damage & Repair below.
* `SYSTEM STATUS`: Vessels have functional components that can be damaged,
  harming the vessel's performance; a system at 100% is fully functional. See
  Damage & Repair below.

Morale
------

Each vessel has a morale value, which starts at a value of 0.0, and can range
from -1.0 to 1.0. Show a vessel's morale with eg `sh s3`. Morale affects a
vessel's combat value by up to 25%, scaling with the morale value linearly. A
vessel is more likely to retreat from combat if morale is low. Events in the
simulation alter morale:

* Participating in combat reduces morale.
* When an enemy retreats, it improves the morale of their opponents.
* When a ship suffers hull damage, this reduces its morale.
* Friendly vessel loss hurts all your ships' morale.
* Enemy vessel loss improves all your ships' morale.

Combat
------

After the movement step of each tick, if any vessels from opposite sides are in
the same location, a round of combat is performed automatically. Ships in
motion engage each other without slowing down; this is often seen when using
`at`.

Each ship has a combat value, an abstract measurement of its weapons and other
tactical capabilities, as modified by damage to these systems and the crew's
morale. This is shown as eg `CV=0.93` in `ls` and `sh` output. The sum of all
the combat values on a side is the total damage inflicted, divided evenly among
the other side's vessels.

The damage inflicted is modified by two randomized factors:

* A die roll determines whether which side gains 'advantage', meaning that side
  got lucky or used better tactics. The advantaged side deals 25% more damage
  and receives 25% less damage.
* Each ship involved in combat may randomly decide to avoid the fight by
  retreating; this is more likely if its Morale is low. A ship that retreats
  both deals and receives half damage (this supersedes advantage).

Retreat results in no movement on the map by default; it's assumed that
retreating ships are using sublight thrust whose displacement at this scale is
negligible. But in the waves-of-raiders scenario, the raiders engage FTL while
retreating, so they run a short way West (-X) back where they came from. After
that, however, they'll resume raiding. This means they can be driven away from
their raiding target.

Damage & Repair
---------------
As with similar games, damage to a vessel is first applied to shields, then any
spillover is applied to the hull. Whenever the hull is damaged, there's a risk
of system damage.

System damage results in harm to the vessel's performance, as shown in a ship's
`sh` output under SYSTEM STATUS. Each system has a percentage that tells its
health as a linear proportion. For instance, `drive: 75%` means the ship can
only travel at 75% of its normal speed. Each system affects a different ship
function:
  * Shields: Maximum shield strength
  * Tactical: Combat value
  * Drive: Warp speed

If, during any tick, a vessel doesn't engage in combat, the crew has time to
effect system repairs. The base rate of repair is shown in `sh`, and is
modified by circumstances:
  * The base rate is used if the ship is in motion.
  * 1.5 x base if holding position via `wt`.
  * 2.0 x base if holding position with a friendly unit present.

Repair work is divided evenly among damaged systems.

Hull damage can't be repaired.
