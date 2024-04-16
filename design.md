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

Interstellar Navigation
-----------------------
Keep basic scale of 64 x 64 grid of space locations. Permit stacking of all
spaceborne objects, except if some exceptional phenomena is encountered (black
hole?).

The 64x64 area is the area of operations; later this will be configurable.
Space is 'smooth'; movement is always calculated as movement between
coordinates. Warp travel is *always* required to move 1+ spaces; impulse drive
is used to improve combat maneuvering and is necessary for orbiting and
de-orbiting.

Combat is between stacked opponents. There's no tactical grid; just the
strategic one.

Warp travel isn't instantaneous. Friendly and enemy ships may be in motion
while other events occur. However, ships can intercept each other, resulting in
fighting at warp. For simplicity, fighting at warp is the same as at sublight
speeds.

Scale & Distance
----------------
Light years for all distances; 1 ly/cell.

In the default scenario, density of natural phenomena and bases is ~1.2
per zone, for a total of about 65-100 immobile objects.

Info on real object density & distance:
* https://en.wikipedia.org/wiki/List_of_nearest_stars_and_brown_dwarfs
* https://en.wikipedia.org/wiki/Stellar_density

Objects & Hazards
-----------------
One way to implement a supernova or black hole: A region around the center
of the object is impassable or otherwise dangerous

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
The simulation runs at 1 tick = 1 hour. This means combat is sometimes
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

The game won't resume running until all idle friendly ships are given orders,
unless the user overrides.
