(both game design and software design)

Game Design
===========
There's already a 'trek' in python 3 in github.

So let's make it interesting: You are in command of a squadron of starships;
say 5 to 8. Each turn you issue commands to each ship to do stuff. If you
skip a ship, it has automatic simple behaviors.

Interstellar Navigation
-----------------------
Keep basic scale of 64 x 64 grid of space locations. Permit stacking of all
spaceborne objects, except if some exceptional phenomena is encountered (black
hole?).

The 64x64 area is a 'sector.' There are no quadrants. Space is 'smooth';
movement is always calculated as movement between coordinates. Warp travel is
*always* required to move 1+ spaces; impulse drive is used to improve combat
maneuvering and is necessary for orbiting and de-orbiting.

Combat is between adjacent or stacked opponents. There's no tactical grid; just
the strategic one.

Warp travel isn't instantaneous. Friendly and enemy ships may be in motion
while other events occur. However, ships can intercept each other, resulting in
fighting at warp. For simplicity, fighting at warp is the same as at sublight
speeds.

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
