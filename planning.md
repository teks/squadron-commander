Iterations
==========

## Iteration 1: Building Blocks
```
[v] spaceborne object base class
[v] basic ship class
[v] map
    [v] (spaceborne) object storage
    [v] distance function
[v] Global simulation class
[v] plan more, clearly
```

## Iteration 2: draft short-ranged map
```
[v] local map command: map <x> <y>
[v] ship designation
```

## Iteration 3: Timekeeping + Friendly ship movement
```
[v] move a ship instantly, disregarding velocity
[v] design FTL system; probably linear hyperspace speed in squares/day
[v] basic UX messaging: simulation emits messages consumed by UX object
[v] basic simulation ticking
[v] after each order to a ship, if untasked ships, list them
[v] move a ship within the simulation's timekeeping
[v] 'run' command with default tick count of 24h = 24 ticks
```

## Iteration 4
fix random stuff, look for TODOs and cleanup:
```
[v] stop using uncommited code as initializer
    [v] it'll need argparse eventually anyway, just do it now
[v] populate the cui labels at startup (later will need to do it at spawn time)
[v] research CLI argument parsing:
    [v] demo argparse
    [v] read about shlex, compare & contrast:
        https://docs.python.org/3/library/shlex.html#module-shlex
    [v] make CLI arg parsing decision
[v] implement arg parsing for CLI based on ---^
```

## Iteration 5
going to do another random fixup iteration
```
[v] various TODOs
[v] cure map viewing pain with `smap`, half-scale map cmd
```

## Iteration 6
add new SBO type: enemy
```
[v] class Enemy(Ship)
[v] change Simulation to have single searchable collection of objects
[v] add enemy to Simulation
[v] add enemy output to Simulation.objects()
[v] add enemy display to short-ranged map
[v] poke around for other bits
```

## iteration 7
combat engine MVP; no encounters yet just mechanics + tests
```
[v] prep Ship for combat (hull, shields, shield recharge
[v] entry point for 1 tick of combat is simulation.combat(units)
[v] Step 1: assign base_combat_value to each ship
[ ] Step 2:
    [v] Compute side CV, choose superior & inferior side; find CV_ratio
    [ ] CRT & simulation.roll_crt()
    [ ] track retreated ships
[ ] Step 3: Compute damage from side CV, applying CRT results
[ ] Step 4:
    [ ] Apply damage to shields then hull
    [ ] check for DESTRUCTION and send messages
[ ] make some ship classes and experiment with combat outcomes
```

## Future Iterations:
```
[ ] combat
    [ ] Step 2: individual ship retreat
    [ ] system damage
        [ ] add systems to ships
        [ ] on hull damage, apply systems damage
    [ ] mull a 'maneuverability' value for ships
    [ ] morale: depletion, restoration, and effect on combat
    [ ] refine ship's combat value (shields down, morale, etc)
    [ ] Step 5: retreat movement
[ ] enemy ships:
    AI-driven enemy vessels' class should be child of Ship;
    enemies assign orders to themselves over time
[ ] attempt to use dataclasses for SpaceborneObject & children
[ ] concrete CLI ux class
    [v] cmd
    [ ] displays for various entities & the map
    [ ] help facility?
```
