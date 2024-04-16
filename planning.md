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
[ ] move a ship instantly
[ ] design FTL system; probably linear hyperspace speed in squares/day
[ ] basic timekeeping, CF `design.md`, Time & Timing
    [ ] after each order to a ship:
        [ ] if untasked ships, list them
        [ ] otherwise, emit clock start message & run clock
    [ ] basic UX messaging: simulation emits messages consumed by UX object
[ ] move a ship within the simulation's timekeeping
```


## Future Iterations:

```
[v] abstract base ux class

[ ] concrete CLI ux class
    [v] cmd
    [ ] displays for various entities & the map
    [ ] help facility?

```
