(both game design and software design)

Game Design
===========
There's already a 'trek' in python 3 in github.

So let's make it interesting: You are in command of a squadron of starships;
say 5 to 8. Each turn you issue commands to each ship to do stuff. If you
skip a ship, it has automatic simple behaviors.

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

* Squares are identified by absolute coordinates, eg '35,53'.
* Zones are overlaid 8x8 grid of squares, with 8x8 squares within each.
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

Combat is between adjacent or stacked opponents. There's no tactical grid; just
the strategic one.

Warp travel isn't instantaneous. Friendly and enemy ships may be in motion
while other events occur. However, ships can intercept each other, resulting in
fighting at warp. For simplicity, fighting at warp is the same as at sublight
speeds.

Objects & Hazards
-----------------
One way to implement a supernova or black hole: A region around the center
of the object is impassable or otherwise dangerous

Combat
------
Mostly follow the trappings of Star Trek: Energy shields, beam weapons,
torpedoes. Each vessel has systems that can be damaged.

Combat between two starships should take "awhile;" it should not feel
instantaneous unless the odds are skewed.

Enemy Behavior & Goals
----------------------
Enemy ships are after colonies and starbases. They will also attack your
squadron. They appear on the map (generally on one side of it) and make their
way to a target, chosen at random at least for now. After destroying it, they
will move on to another.

Detection
---------
For now, starbases, ships, and colonies have a simple binary detection radius.
Enemies are either detected or hidden.

When an enemy vessel becomes hidden, its last known position will be retained,
possibly showing a vector.

Time & Timing
-------------
It's simple event-based timing, and runs until it needs to pause. These events
generate a pause:

* Friendly unit sights a previously hidden enemy
* A unit arrives somewhere (friendly or enemy)
* A ship's orders expire: It destroys its target, finishes repairs, etc.
* Others as-needed

If needed, maybe implement user-configured pausing or regular pausing.

The game won't resume running until all idle friendly ships are given orders,
unless the user overrides.

Software Design
===============
```
Game/Simulation: instance to manage everything
    Map: 64 x 64 grid
        contents: dict of (Point -> object)
```
