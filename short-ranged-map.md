
Character codes for the short-ranged map; these are also used in input eg `scan <code>`

One unambiguous two-letter code for each object. The second char appears to the
right in the blank space, eg `*A` for star A.

Letters are case-insensitive for input but shown as a capital letter (they're
more clear). So, can't use small letters. Also 'Z' used in displays is used to
mean that the designation can't fit in a single character.

When a star and one other object share a cell, the object takes precedence.

TODO: occupied system vs. unoccupied system? 

## Codes
```
Most important, needed right now
.   empty cell
:7  multiple contacts; in this case 7 in the cell
    (natural phenomena like stars aren't counted for this purpose)
    TODO perhaps for multiple contacts which includes natural phenomena: ;7
*A  star A
!C  enemy C
^3  Squadron member 3

Implement/clarify later:

?G  Unknown object G

settlements:
    %7 starbases & spaceborne colonies
    #5 planetary settlement (looks like a farm) :]

first character can be a letter too:
    x5  squadron member 5
    b8  starbase 8
    various letters can be used for classes of enemies perhaps
        maybe use letters for ALL vessels, bases, and settlements?

unused chars
    basic symbols:  - ~ | / \ ; : 
    paired symbols: ( ) [ ] { } < >
    lots of letters
    @ a big object, say, a black hole?
    ; don't use, too much like :
    don't use these chars, too visually indstinct: ` ' " , _
```
