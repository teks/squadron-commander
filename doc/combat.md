Combat
======
A unit is any object that can be damaged by combat; in this file often 'ship'
is used but starbases, space colonies, and even planetary settlements are
treated similarly.

Units have shields and hull values, which are both treated as hit points;
damage drains shields first. `hull = 0` indicates the unit is functionally
destroyed (though there may be survivors and salvage).

Weapons and other tactical capabilities, eg targeting scanners and damage
control, all lumped together and treated abstractly, as the unit's 'combat
value.' At the moment, weapons can't miss and can't be dodged. This is
intentional as the ships are presumed to maneuver much worse than high-tech
weapons' ability to hit their targets.

Combat is unaffected by FTL; two vessels at warp can fire on each other
normally.

A vessel may retreat from combat using its warp drive, but it must do
so at maximum power. Thus a ship has a warp acceleration value, representing
both its literal acceleration and also activation latency.

Mechanics
---------
Combat is resolved automatically as the player has no direct control over a
ship's moment-to-moment operations.  Combat is fast enough that it often
resolves in a single tick (in 1 hour).

The squadron commander can issue these combat orders to a ship:
* Toggle `evasive` boolean: if True, and it has a warp drive, the unit
  automatically retreats from fights.
* Attack an enemy. This will cause movement and interception as needed.
  While the enemy is in combat with the ship, the ship will ignore `evasive`.

Combat is implemented in steps each tick, based on these factors:

* Each side has its set of vessels, each having its properties & state
* Nearby static units, including friendly bases and settlements

Combat Resolution Steps
-----------------------
### Assemble Sides

All units in the same position automatically take part in combat each tick (the
two ponts must be exactly equal; the map is in light years). Sort all such
units into a friendly side and an enemy side.


### Compute Combat Value

A unit's base combat value is modified by damage, morale, and the state of its
shields (shields are restored after combat, unless they're damaged).

Compute a CV for each side; for now just sum the units' CVs.

### Assign Advantage

Each combat tick, one side or the other may outmaneuver or otherwise
gain an advantage over the other. There's an equal chance of each:

* friendly side gets the advantage
* enemy side gets the advantage
* Neither side gets the advantage.

If a side has the advantage, its combat rating increases 25%; the opposing side
loses 25%.

If crews are ever given variability, better crews would increase the chance to
gain the advantage.

### Retreat Checks

A ship retreats if its `evasive` flag is set. Otherwise, it may choose to
retreat if the ratio between the two sides' CVs is unfavorable. The chance of
retreat grows as the ratio worsens.

The chance of retreat is affected by eg morale; other specific influences may be
added, such as hull damage or shield depletion. If a ship is protecting a base or
settlement, chance of retreat likewise declines.

Note which ships have retreated as they will inflict and receive reduced damage.

### Assign Damage

Damage effects are applied simultaneously so there's no need for an initiative
system:

1. Compute the total damage dealt to each side:
    * Each ship's damage dealt is equal to its CV * adjustment. Adjustment
      equals:
        * 0.5 if the ship is retreating, or else:
            * 0.75 if ship has disadvantage
            * 1.25 if ship has advantage
    * Sum the damage from each side and apply it to its opponent.
1. Compute the damage received by each ship:
    * Divide the side's received damage equally among its units.
    * Any ships that are retreating receive 50% damage.

If ships get a maneuverability or sublight speed value, then slower ships will
tend to draw fire away from faster ones, as the faster ones can dance out of
range more effectively if other ships are threatening their pursuers.

### Apply Damage

Once the shields are down, mostly, you're fucked.

Damage is first applied to shields, then to the ship's systems; for ideas, cf
"Damage to specific systems" in `ega-trek-design-notes.md`.

Whenever Damage is applied, first shields are reduced by that quantity. Any
leftover is applied to the ship's hull. Once the hull is reduced to 0, the ship
is destroyed.

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

#### Wear and Tear and Maintenance

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

### Perform retreat movement

Any surviving ships that are retreating are moved a short distance away from
the battle. Each ship's warp acceleration value is used for this.  Ships from a
side tend to retreat in the same direction.

This separation should be enough to force pursuing ships to chase for multiple
ticks _if_ their speeds are very similar. The distance should be short enough,
though, that a 'free move' outside of normal movement shouldn't break the
simulation.

Implications
------------
* There's not much difference between one big ship and several small ones,
    provided the sum of their CVs, shields, and hulls are the same.
* However, fights with fewer big ships are more swingy than those with
    many small ships, because more chances for retreat results in a more
    average performance.

### Value Sculpting & Outcomes
Garaunteed kill, regardless of side's advantage (double if target is retreating):
`CV needed >= 4/3 * (target's shields + target's hull)`.

*Ship Designs* will thus need to have CVs that are double a typical (shields +
hull) for most fights to be over in one tick. Likewise a disadvantaged foe will
tend to retreat, reducing their own damage.

*Hull* is (or will be) very different from shields:
* Some vessels may have powerful shields and weak hulls, or more rarely, vice versa.
* In the field, shields easily recharge, but hull is very difficult to repair.
* Hull damage will later result in system damage.

### How does the player win a prolonged defense of the sector?

The enemy, being engaged in raids, likely has worse ships than the
player. Also, the player has access to facilities; the enemy does not.
If the influx of enemies is paced correctly, the player ought to have
time to send a ship back for repairs.

