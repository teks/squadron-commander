
### one line object display

Presently (post i10) it shows:

```
!0 klaybeq    (32.00, 32.00) CV=1 [###])))  ATTACKING @1 New Ceylon (40.00, 12.00)
```

Shield & hull display:
* `[###]` hull is >75%, `[   ]` hull is <25%
* `)))` shields at maximum, `)  ` shields nearly down, `   ` shields down
* `[###])))` everything great

### detail object display

First line the same:
```
!0 klaybeq    (32.00, 32.00) CV=1 [###])))  ATTACKING @1 New Ceylon (40.00, 12.00)
    Vulture Class
    Velocity:               N.N / N.N
    Shields:        NN%     N.N / N.N
    Damage Report:
        Hull:                53%    5.3/10.4
        FTL Drive:          100%
        Tactical Systems:   100%
        Shield Generators:  100%
    Morale: <in-universe statement from the captain here> (n)
```

Nice-to-haves:
* `ATTACK <tgt>, intercept at (x, y), (+x, -y), Heading WNW, ETA 1h`


### previous one-line display ideas

graphical display, where ) and ] graphically suggest shields & hull
```
# graphically suggest ship surrounded by shields; symmetrical:
^2 baker      (35.00, 30.00) -> (53.00, 42.00) CV:n (  [nn] n)
# same thing but asymmetrical
^2 baker      (35.00, 30.00) -> (53.00, 42.00) CV:n ([nn]nn)

# graphical shields, health bar hull
^2 baker      (35.00, 30.00) -> (53.00, 42.00) CV7 ((([###])))
# minimal shields, some hull damage
^2 baker      (35.00, 30.00) -> (53.00, 42.00) CV7   ([## ])

# same thing but <> for hull, suggests cool angular ship
^2 baker      (35.00, 30.00) -> (53.00, 42.00) CV7  ((<###>))  

# special symbol for shields down?
# this means shields low:   ([## ])
# this means shields down:  ![## ]!
^2 baker      (35.00, 30.00) -> (53.00, 42.00) CV7  ![## ]!
```

