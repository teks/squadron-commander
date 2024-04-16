## Representing heading & speed and/or destination on the short-ranged map

3 pieces of info to represent

* Speed & heading: predictive markers
* Destination: destination marker?

### predictive markers

Has the advantage of info visually near its object while giving info on
both speed and heading (but not destination).

When the UX is visible between ticks, there are no planned moves, but basically
the first marker is the planned move, and the next one is the next planned move.

```
34 . . . . . . . . .
   . x . . . . . . .
32 . . x x !0. . . .
   . . . . . . . . .
30 . . . . . . . ^2.
   . . . x . x . . .
28 . x . . . . . . .
    29  31  33  35
```

```
34 . . . . . . . . .
   . + . . . . . . .
32 . . + + !0. . . .
   . . . . . . . . .
30 . . . . . . . ^2.
   . . . + . + . . .
28 . + . . . . . . .
    29  31  33  35
```


### extra chars

Grab unicode chars?

```
34 . . . . . . . . .
   . . . . . . . . .
32 . . . . !0. . . .
   . . . . . . . . .
30 . . . . . . . ^2.
   . . . . . . . . .
28 . . . . . . . . .
    29  31  33  35
```

### destination marker
* problem with destination markers is user has to search for them visually
* say + for friendlies, x for enemies
* or paired letters (change ! and ^ to letters): say E2 is headed for e2


## Character codes

Character codes for the short-ranged map; these are also used in input eg `scan <code>`

One unambiguous two-letter code for each object. The second char appears to the
right in the blank space, eg `*A` for star A.

When a star and one other object share a cell, the object takes precedence.

TODO: occupied system vs. unoccupied system? 

### Codes
```
Most important, needed right now
.   empty cell
:7  multiple contacts; in this case 7 in the cell
    (natural phenomena like stars aren't counted for this purpose)
    TODO perhaps for multiple contacts which includes natural phenomena: ;7
*A  star A
!C  enemy C
^3  Squadron member 3
%7  starbase 7
@3  space colony 3

Implement/clarify later:

?G  Unknown object G

settlements:
    #5 planetary settlement (looks like a farm) :]
        o5 alternate perhaps; looks like a planet

first character can be a letter too:
    x5  squadron member 5
    b8  starbase 8
    various letters can be used for classes of enemies perhaps
        maybe use letters for ALL vessels, bases, and settlements?

Black hole?  I dunno what it would do mechanically anyway so forget it for now, but:
    O   don't think I need O for anything (not showing individual planets)
    ()  multiple chars gives nice impression of unusual size

how do I feel about unicode?

unused chars
    basic symbols:  - ~ | / \ ; :
    paired symbols: ( ) [ ] { } < > ^ v
        save ( ) [ ] { } for targetting brackets?
    lots of letters:
        a-z A-Z

unusable chars
    don't use these chars, too visually indstinct: ` ' " , _
```
