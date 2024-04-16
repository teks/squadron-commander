Pursuit and Interception
========================

Say F is attacking E but first needs to intercept it. Each tick F needs to
decide where to move to close the distance.

Solved cases:
* E is stationary: Trivially move directly toward F.
* E is moving to a specific location: Plot an intercept course.
* E is attacking an immobile unit: Plot an intercept course.
* E and F are targeting each other; they meet along the line between them


Circular Pursuits Case
----------------------
For now, enemies aren't permitted to attack mobile friendly units, so there can
be no chance of this problem. But it would be a nice feature to have.

Say several ships are pursuing each other, such that the chain of
pursuits is circular:

```
Fa -> Ea -> Fb -> Eb -> Fc -> Ec -> Fa -> Ea -> ...
```

How does Fa choose where to move each tick? It can't close distance with Ea
until it knows Ea's heading. Ea's heading is dependent on Fb's heading, and so
on, such that Fa can't know its own heading unless it knows its own heading.

The fundamental problem is that each tick is internally simultaneous whereas in
real life it is an hour, in which judgement calls can be made and courses
changed.

### Solutions

* A tick being an hour, assume there's time within to adjust course after
  observing what other ships are doing. Therefore let each ship observe its
  target's planned move while planning its own move. Introduce a way to
  sequence move planning so somebody goes first, which should let dependencies
  resolve.
* Because there are two sides, everyone involved in a circular pursuit can be
  reorganized into two sides, and destinations chosen accordingly.
