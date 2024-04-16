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

### Compute Combat Value
Each ship has a base combat value (CV), reflecting its firepower and other
strengths. This value is modified by damage, morale, and the state of its
shields (shields are restored after combat, unless they're damaged).

```
def cv(self):
    """Compute the unit's combat value."""
    return f(self.base_cv(), self.damage, self.morale, self.shields)
```

Compute a CV for each side; for now just sum the units' CVs.

### Assign Advantage

Each combat tick, one side or the other may outmaneuver or otherwise
gain an advantage over the other. There's an equal chance of each:

* friendly side gets the advantage
* enemy side gets the advantage
* Neither side gets the advantage.

If a side has the advantage, its combat rating increases 25%; the opposing side
loses 25%.

### Retreat Checks

The inferior side may choose to retreat if the ratio between the two sides'
CVs is very unfavorable. The chance of retreat grows as the ratio worsens.

A ship may decide to retreat even though its allies don't, so also perform a
similar retreat check for each individual ship on both sides.

The chance of retreat is affected by eg morale; other specific influences may be
added, such as hull damage or shield depletion.

Note which ships have retreated as they will inflict and receive reduced damage.

### Assign Damage

Each ship is damaged; retreating ships receive less. Damage effects are applied
simultaneously so there's no need for an initiative system.

1. Compute the total damage dealt to each side:
    * Each ship's damage dealt is equal to its CV * adjustment. Adjustment
      equals the first that applies:
        * 0.5 if the ship is retreating
        * 0.75 if ship has disadvantage
        * 1.25 if ship has advantage
    * Sum the damage from each ship and apply to the other side.
1. Compute the damage received to each unit:
    * Divide the side's damage received equally among its units.
    * Any ships that are retreating receive 50% damage.

If ships get a maneuverability or sublight speed value, then slower ships will
tend to draw fire away from faster ones, as the faster ones can dance out of
range more effectively if other ships are threatening their pursuers.

### Apply Damage

Once the shields are down, mostly, you're fucked.

Damage is first applied to shields, then to the ship's systems; for ideas, cf
"Damage to specific systems" in `ega-trek-design-notes.md`.

Damage is applied as a single number. It will first ablate the shields. Any
leftover is applied to the ship's hull. Once the hull is reduced to 0,
the ship is destroyed.

Also, any time the hull is damaged, crew morale is harmed as well.

### Ship System Damage
Every tick of combat in which the hull is damaged, there's a chance to damage
each of a ship's systems. Each system is subjected to a separate roll:
* Chance of damage grows with hull damage fraction.
* Severity of damage also grows with hull damage fraction.

Each system's health is tracked separately as a fraction (1.0 = undamaged).
The fraction is used to know how the system's performance is degrading.

List of systems to damage and the effects of damage:
* Shields: Damage reduces maximum and charge rate
* Warp Drive: Reduced speed and energy efficiency
* Tactical Systems: Reduced combat value

### Perform retreat movement

Any surviving ships that are retreating are moved a short direction and
distance away from the battle; distance is adjusted by the ship's emergency
speed value. Ships from a side tend to retreat in the same direction.

This separation should be enough to force pursuing ships to chase for multiple
ticks _if_ their speeds are very similar. The distance should be short enough,
though, that a 'free move' outside of normal movement shouldn't break the
simulation.

