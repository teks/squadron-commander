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
[ ]
[ ]
[ ]
[ ]
[ ]
```

## Future Iterations:

```
[v] abstract base ux class

[ ] concrete CLI ux class
    [v] cmd
    [ ] displays for various entities & the map
    [ ] help facility?

```
