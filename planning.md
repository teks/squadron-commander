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

## Future Iterations:
```
[ ] concrete CLI ux class
    [v] cmd
    [ ] displays for various entities & the map
    [ ] help facility?
```
