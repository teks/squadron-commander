
EGA Trek Docs
=============
```
EGATREK.DOC     Documentation (instructions)
EGATREK.REF     Quick command reference
```

EGA Trek Design
===============

8x8 quadrants to secure

Difficulty
----------
> higher levels must contend with more enemy ships and with more abilities
> and phenomena in the enemy.

Ship
----
"387" crew and "43" officers

Energy
* Generates 400 / stardate
* Military ops is generally much higher than this

Warp drive:
* safe cruising speed: warp 6
* emergency speed:     warp 8
* Damage causes max warp to drop
* Warp drive with the shields raised costs double energy

Weapons
* Beam Weapons: "3 banks/2 each"
  * damage attenuated by range
  * can overheat (watch meter)
  * there's also an 'effectiveness' meter (overheat + damage)
* Torpedoes:    3 tubes, 9 in storage
  * At close range, one-hit kill; less effective at range
  * accuracy thrown off by shields being raised
* Death Ray: an unproven superweapons, *may* destroy every ship in the quad.
* Self destruction: May take a few enemies with you

Shields
* Enemy fire drains shield energy and damages the ship
* But at 100%, no ship damage
* Raising shields causes small energy loss; lowering does not

Long-range Scanners
* Computer remembers what you've seen in a galaxy chart
* Damage causes loss of detection small things first, so ships, then stars
* MFS:
  * Mongol count
  * Friendly starbase type: 1 Starbase, 2 research station, 3 supply depot
  * Star count
  * 999 is a supernova

Comms, external and internal are integrated:
* Acknowledge each message with a key press
* department shown for each message
* Hailing a base requires time for signal propagation

Exploration
* Planets may have energium
* "regulations [require] your shields must be under 50% and main energy
under 20%."
* First, orbit, then land, choosing either transporters or shuttlecraft
* Orbiting allows the planet to be scanned

Damage & Repair: As for a damage report with estimated times to fix.  Repair
speed varies, and is faster at a StarBase:
```
1x    Normal repairs, work evenly divided among systems
2.5x  Normal repairs while docked at a starbase
3x    Repairing only a selected system
5x    Repairing a selected system while docked at a starbase

Damage to specific systems:
   EnergyConverter: The ship's energy converter generates energy
     for the ship at a rate of 400 units/day times percentage of
     repair.
   Shields: The shields percentage of repair indicates how
     efficiently the shield generators can convert the energy
     available in the shield system into actual shielding of the ship.
   Warp Engines: The warp engines are virtually impossible to
     destroy completely, but their level of damage affects the maximum
     possible warp speed.  The maximum warp speed is approximately
     warp 1 plus 0.09 times percentage of repair.
   Impulse Engines: Impulse engines are much simpler than warp
     engines; they either work or they don't.  When they are at less
     than 50% they simply stop functioning.
   Lasers: Laser percentage of repair is a direct indication of
     what percentage of energy is converted to destructive force at
     the point of impact.  In other words, for a given level of laser
     energy, 100% working lasers will do twice the damage of 50%
     working lasers.
   EnTorp Tubes: Like impulse engines, torpedo tubes either work or
     they don't.  At 100% there are three functional tubes, 67-99% only
     two tubes work and 34-66% only one. 
   Short Range Scanners: Short range scanners lose resolution when
     they are damaged.  Above 90% they are fully functional, but below
     90% they are unable to detect anything smaller than a star.
     Below 50% they do not function at all.
   Long Range Scanners: Long range scanners also lose resolution
     when damaged.  When less than 100% repaired they can no longer
     detect enemy ships.  Below 50% they are not functional.
   Computer: A modern starship is highly computerized, so loss of
     computer function affects a number of things.  Portions of the
     ships charts can be lost if the computer is sufficiently damaged
     and can only be recovered by re-scanning.  Automatic navigation
     requires the computer to be 100% repaired.
   Life Support: Life support systems must be 100% to generate food
     and oxygen needed to sustain life.  Without a functioning life
     support system the ship can last only two days on reserves.
   Transporter:  The transporter must be at 100% to be used.
   Shuttlecraft:  The shuttlecraft must be at 100% to be used.
```

Bases
-----
TODO: Does 'life support supplies' mean energy?
> A StarBase is the most useful because you can replenish all ships supplies
> there.  Supply stations can provide life support supplies and energy
> torpedoes.  Research stations can provide only life support supplies.  You
> are responsible for the protection of all bases in your designated area.

While docked, its shields will protect your ship.

UX
==
CF egatrek.doc, 'COMMANDS'

```
move v,h,v,h # move to quadrant & sector
move v,h    # move to sector (within current quadrant)
dock        # dock at starbase adjacent
warp n      # go this fast for next move
energy      # re-allocate energy
```
