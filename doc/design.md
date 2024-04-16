(both game design and software design)

Game Design
===========
There's already a 'trek' in python 3 in github.

So, to make this game unique: The player commands a squadron of starships;
say 5 to 8. As the 'SQC' or 'squadcom,' they issue commands to each ship, but
they don't have fine-grained control of the ship's internal processes.

Should I rescale to one solar system?
-------------------------------------
For now I'm not sure so stick to the original plan.

4h to 8h to cross the solar system at 1.0c:
* 30 AU from the Sun to Neptune = 0.00047 light-years = 4.16 hours' travel
* So about 8 hours to cross from outermost planet (Neptune) to its antipode.
* This is fast enough that one can neglect orbital motion of planets & other bodies:
  In the Solar System, the rocky planets orbita periods are 88d - 687d.

Invader motivations and general activity would be the same: Destroy bases and
settlements.

The star system should be sparsely populated, with little industrial basis, to
avoid introducing a scale problem: If it's Earth, there's a huge industrial
base, thus any serious threat to the Solar System would have to be massive.

Reasons to do it:
* More realistic in some ways: Can credibly be 2D but still set it in space
* 'slow' high-speed travel (>=1c) is still relevant as it cuts down transit
  time (eg still several hours to get from Earth to Jupiter).
* Has "planetary cool" instead of "interstellar cool"

Reasons not to do it:
* Not as many locations:
  * Interstellar case: 64 zones -> 50 to 60 star systems and other points of interest
  * Planetary case: 8 planets + an inner asteroid belt + an outer comet belt +
    several La Grange points -> 8 + 3 + 5 + 10 = 26 places for colonies/bases
    (but that's not bad actually)
* May be difficult to represent in plain text
* planned grid reference system makes no sense if everything is in motion (even
  if the motion isn't modelled)
* becomes less like a chess match and more like some kinda orrery game


Spatiodesy
----------
+X is always to the right; +Y is always up. When letters are used instead of
numbers, lexicographic order is considered to be ascending (ie A, B, C...).

* Cells are identified by absolute coordinates, eg '35,53'.
* Zones are overlaid 8x8 grid, with 8x8 cells within each.
* When needed, letter-based coordinates ('AB') are used for identifying a zone.

Zones are mostly used for the large-scale map and its grid of '123' displays
for each zone.

The high-resolution display shows a 3x3 grid of zones (24 rows x 48 columns).

Possibly support `<zone>-<grid>` addressing, eg 'CD-12,15' or similar.

Spatiolocation
--------------
A point in space is a pair of floats, `(x, y)`; ordinary two-dimensional
geometry applies normally, such as the distance formula.

But floating-point math is unreliable. Occasionally there will be two different
ways of computing the same value, but two slightly different values are
returned. Generally the difference is small, say 10^-12, but it can still cause
problems. So, `a.point == b.point` is not sufficient to tell whether
two objects are "in the same place" because of these tiny variations.

For the case of intentionally travelling to an object instead of a location,
the code can carefully `traveller.point = object.point`. This way `==` can be
made to be reliable.

Also observe that in the vastness of space, it's extremely unlikely that two
vessels would encounter each other by accident.

So for both technical and physical reasons, ideally, special circumstances are
required for a rendezvous:
* One successfully intercepts another.
* Several vessels are travelling together.
* Two vessels are intentionally seeking each other.
* Vessels are congregating at a location, such as a planet.

### `math.isclose(a, b)` May Be Close Enough

`math.isclose(a, b)` is `True` when a and b are within a high relative
tolerance of 1e-09. But sometimes three or more objects must be tested for
colocation, but `isclose(a, b) and isclose(b, c) and not isclose(a, c)`.
That's nonsense: Colocation should have the transitive property.

However, if floating point deviations have much smaller magnitudes, only a
great many of these deviations taken together could reach the scale of
`isclose`'s default tolerance (imagine a series of objects in a row). So for
now, use `isclose` to detect colocation, and carefully watch for violations of
the transitive property.

### `isclose(a, b)` Graphs to Emulate The Transitive Property

One can find _all_ the chains of closeness betwen all the objects on the map,
and thus assemble a set of graphs. Each represents a set of objects that are
roughly "in the same place." The maximum distance between any two members of
such a graph would be `1e-9 * n`, where n is the maximum number of objects a
graph can have.  It's possible to reach ten such objects, but not a hundred, so
the worst case would have an effective tolerance smaller than `1e-8`.

Interstellar Navigation
-----------------------
Area of operations is 64 x 64 light years; later this will be configurable.
Permit stacking of all spaceborne objects, except if some exceptional phenomena
is encountered (black hole?).

Space is 'smooth'; movement is always calculated as movement between
coordinates. Warp travel is *always* required to move 1+ spaces; impulse drive
is used to improve combat maneuvering and is necessary for orbiting and
de-orbiting.

Combat is between stacked opponents. There's no tactical grid; just the
strategic one.

Warp travel isn't instantaneous. Friendly and enemy ships may be in motion
while other events occur. However, ships can intercept each other, resulting in
fighting at warp; see `interception.md` and `combat.md`.

Scale & Distance
----------------
Distances are in light years.

In the default scenario, density of natural phenomena and bases is ~1.2
per zone, for a total of about 65-100 immobile objects.

Info on real object density & distance:
* https://en.wikipedia.org/wiki/List_of_nearest_stars_and_brown_dwarfs
* https://en.wikipedia.org/wiki/Stellar_density

Objects & Hazards
-----------------
Star Systems are the primary locations for settlements (planetary or orbital
colonies) and starbases.

Perhaps the contents of a star system, whatever is nearby a raider target,
affect battles that happen there:
* planets & moons: can hide behind planet to help retreat
* gas giant: risk of encountering atmosphere, especially if damaged

Other objects may be developed later, such as black holes and supernovae. If it
makes sense for these to be dangerous, the danger would be expressed as a
radius from their position, or a function of the radius for declining danger
further out.

As the game is science fiction, objects and dangers can of course be invented
for gameplay purposes. Maybe leviathans or behemoths, giant creatures that
prowl the void.

Nebulae are too large to fit on the map. One use of changing the game's scale
to a single star system is all the interesting locations such as asteroid belts
can be added.

Combat
------
See `combat.md`.

Enemy Behavior & Goals
----------------------
Enemy ships are after colonies and starbases. They will also attack your
squadron. They appear on the map (generally on one side of it) and make their
way to a target, chosen at random at least for now. After destroying it, they
will move on to another.

Detection
---------
Assume good sensors permit the entire area of operations to be perfectly
visible at all times.

Later, consider adding in sensor ranges, detection, and stealth. So, starbases,
ships, and colonies would have a simple binary detection radius.  Enemies are
either detected or hidden.

When an enemy vessel becomes hidden, its last known position will be retained,
possibly showing a vector and status (ie vessel type and any known damage).

Time & Timing
-------------
The simulation runs at 1 tick = 1 hour. This means combat is often
resolved in a single tick.

It's simple event-based timing, and runs until it needs to pause. These events
generate a pause:

* A new unit spawns (say an enemy in the spawn zone of the map)
    * semi-related: if the squadron loses a ship, should it be replaced?
* A unit arrives somewhere (friendly or enemy)
* A ship's orders expire: It destroys its target, finishes repairs, etc.
* Others as-needed

If needed, maybe implement user-configured pausing, regular pausing to
emulate turns, or maybe timeouts, ie, 'run for 1 day.'

The game won't resume running until all ships controlled by the player have
orders, unless the user overrides.

### Processing 1 Tick of Time

Each tick has several internal steps:
1. Plan movement: Each unit plans picks its destination point for the tick.
2. Movement: Each unit is moved to its new position.
3. Combat: Any colocated hostile units engage in combat.
4. Post-action:
    * AI-controlled units are given new orders if needed.
    * If a unit did not fight this turn, its shields recharge.
    * Other cleanup or post-combat activity is performed.

Ship Engineering & Repair
-------------------------
CF `doc/combat.md` under Apply Damage and Ship System Damage.

### Repair

Similar to EGA Trek, each ship has a repair rate (small nonnegative float),
representing progress made each tick. Progress is random based on this value.
Circumstances affect progress made; from worst to best:
* no progress on a combat tick; engineering staff is busy :P
* x1.0 FTL in open space (but progress on the FTL drive is perhaps 0.5x)
* x1.5 waiting alone
* x1.5 waiting with a friendly:
    * all local friendlies pool their repair rate for use among damaged vessels
    * so an undamaged vessel donates its repair crews to a nearby damaged ally
* best is dedicated facilities like shipyards; multiplier TBD

Simple version for the beta: Progress is deterministic and equal to the
vessel's repair rate, divided evenly among the damaged components (this
sometimes results in losses). Progress modifiers:
* no progress on a combat tick
* x1.0 FTL
* x1.5 waiting alone
* x2.0 waiting with a friendly (n friendlies together means x2.0 for each of them)

### Wear and Tear and Maintenance

Starships are advanced superluminal vessels, and are optimized for performance,
not low maintenance.  During travel and most other operations, a ship gradually
accumulates wear and tear. Eventually system damage results.  To avoid these
breakdowns, a ship must regularly return to a starbase or similar facility for
maintenance.

Activities sorted by lowest accumulation to highest:
1. No wear while docked at a starbase
2. Idle in space or performing low-intensity ops (in orbit, investigating a nebula)
3. At warp, cruising speed or less
4. High warp
5. In combat
6. Maximum warp
