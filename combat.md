Combat
======
Mostly follow the trappings of Star Trek: Energy shields, beam weapons,
torpedoes. Each vessel has systems that can be damaged.

Combat is resolved automatically as the player has no direct control over a
ship's moment-to-moment operations.  Combat is fast enough that it rarely
requires a full day, and often resolves in an hour.

The squadron commander can issue these combat orders to a ship:
* Attack an enemy (this will cause interception as needed).
* Attempt escape from combat (this will likely cause pursuit).

Mechanics
---------
Combat is implemented in two steps each tick.

First, similarly to an old-school combat results table, an outcome is
computed from these possibilities:

* victory, foes retreat
* draw, both sides retreat
* defeat, friendlies retreat
* battle continues for an additional tick

I may change this to a per-ship retreat check.

The check or roll is influenced by:
* The ratio of the two sides' combat values
* Whether shields are up or down
* Stakes, ie, whether a ship is protecting something

Each ship has a base combat value, reflecting its firepower and other
strengths. This value is modified by damage and morale.

Second, damage is computed; each participant fires upon a foe, and if it
penetrates the sields, its systems are damaged. This in turn degrades the
combat value used to roll on the combat results table.

Following Star Trek's model, ships generally can't evade fire. Instead, high
sublight acceleration is used to increase the chances of successful retreat.
Also slower ships tend to draw fire away from faster ships, as the faster
ones can dance out of range more effectively if other ships are threatening
their pursuers.
