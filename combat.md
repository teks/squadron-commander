Combat
======
Mostly follow the trappings of Star Trek: Energy shields, beam weapons,
torpedoes. Each vessel has systems that can be damaged.

Combat is resolved automatically as the player has no direct control over a
ship's moment-to-moment operations.  Combat is fast enough that it often
resolves in a single tick (in 1 hour).

The squadron commander can issue these combat orders to a ship:
* Attack an enemy (this will cause interception as needed).
* Attempt escape from combat (this will likely cause pursuit).

Mechanics
---------
Combat is implemented in steps each tick, based on these factors:

* Each side has its set of vessels, each having its properties & state
* Nearby static units, including friendly bases and settlements

### Step 1: Compute Combat Value
Each ship has a base combat value (CV), reflecting its firepower and other
strengths. This value is modified by damage, morale, and the state of its
shields (shields are restored after combat, unless they're damaged).

```
def cv(self):
    """Compute the unit's combat value."""
    return f(self.base_cv(), self.damage, self.morale, self.shields)
```

### Step 2: Combat Results Table & Retreat Checks

Compute a CV for each side; for now just sum the units' CVs.

Find the ratio of `superior_side_cv / inferior_side_cv`; in case of a tie
assume the player's side is superior.  Roll on the combat results table (see
'pytrek CRT' google sheet), which will give a damage adjustment for each side.

After this, perform retreat checks for each individual ship; a ship may need
to retreat even though its allies don't.

The chance of retreat is affected by influences such as morale; it may be
necessary to tweak this chance to emphasize specific influences such as low or
damaged shields.

Note which ships have retreated as they will have receive reduced damage.

### Step 3: Combat Damage Assigned

Each ship is damaged; retreating ships receive less. Damage effects are applied
simultaneously so there's no need for an initiative system.

1. Compute the total damage dealt to each side:
    * For now use each ship's CV as its damage dealt; sum these values.
    * A retreating ship contributes half its normal damage.
1. Compute the damage received to each ship.
    * Divide the side's damage received equally among its units.
    * Any ships that are retreating receive reduced damage (see 'pytrek CRT'
      google sheet).

Damage is first applied to shields, then to the ship's systems; for ideas, cf
"Damage to specific systems" in `ega-trek-design-notes.md`.

If ships get a maneuverability or sublight speed value, then slower ships will
tend to draw fire away from faster ones, as the faster ones can dance out of
range more effectively if other ships are threatening their pursuers.

### Step 4: Apply Damage

Once the shields are down, mostly, you're fucked.

Damage is applied as a single number. It will first ablate the shields. Any
leftover damage is applied to the ship's hull. Once the hull is reduced to 0,
the ship is destroyed.

Every tick of combat in which the hull is damaged, there's a chance to damage
a ship's systems, say 50%. List of systems to damage and the effects of damage:

* Shields: Damage reduces maximum and charge rate
* Warp Drive: Reduced speed and energy efficiency
* Tactical Systems: Reduced combat value

Also, any time the hull is damaged, crew morale is harmed as well.

### Step 5: Perform retreat movement

Any surviving ships that are retreating are moved a short direction and
distance away from the battle; distance is adjusted by the ship's emergency
speed value. Ships from a side tend to retreat in the same direction.

This separation should be enough to force pursuing ships to chase for multiple
ticks _if_ their speeds are very similar. The distance should be short enough,
though, that a 'free move' outside of normal movement shouldn't break the
simulation.

