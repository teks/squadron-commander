Squadron Commander
==================

Command a squadron of starships to protect a region of space. This is yet
another game in the tradition of trek games, originally founded by Mike
Mayfield in 1971:

https://en.wikipedia.org/wiki/Star_Trek_(1971_video_game)

The version I played the most as a kid, and referenced the most while designing
this one, was the terrific EGA Trek by Nels Anderson.

Unlike most trek games, in this version the raiders move and act on their own,
rather than remaining still, and instead of searching for them, one intercepts
them as they raid vulnerable space stations. Run `waves-of-raiders.py` to play
a demo scenario.

`HOWTOPLAY.md` is the game's manual. See also Screenshot below.

Development
-----------

It is written in pure python (tested on python 3.11.5), with no dependencies
unless you want to run the test suite (see below). `waves-of-raiders.py`, being
a short script, is a good entry point for understanding the code and how to
write your own scenarios and other content such as custom ships.

`planning.txt` lists all the work not done and the great many bugs unfixed;
nevertheless I swear I've never worked for Bethesda.

To run the test suite:

```
pip install -r requirements.txt
PYTHONPATH=`pwd` pytest
```

`design/` contains design notes, including many unused ideas.

"Screenshot"
------------

```
% ./waves-of-raiders.py
Squadron Commander: A 2D interstellar wargame,
   inspired by the 'trek' games of the 70s and 80s.
   'help' or '?' to get started; try 'sm' to view the field of play.
   Release version: 0.1.0-beta
0h> sm
64 . . . . . . . . . . . . . . . . . . . . . s1. . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
60 e1+ . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
56 . . . . . . . . . . . . . . . . . . . . . . . . . c2. . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
52 . . . . . . . . s2. . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
48 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
44 . . . . . . . . . . . . . . . . . . . . . s0. . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
40 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
36 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
32 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   e0+ . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
28 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
24 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
20 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . s3c3. . . . . . . . . . . . . . . .
16 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
12 . . . . . . . . . . . . . . . . . . . c0. . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . c1. . . . . . . . .
 8 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
 4 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
   . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
     4   8  12  16  20  24  28  32  36  40  44  48  52  56  60  64
0h> sh s3
s3 Defender-4 (30.00, 18.00) W=1.00 CV=1.00 [###])))  NO ORDERS
    Base Repair Rate: 1% / hour        Morale: 0.00
    SYSTEM STATUS
        shields:  100%
        tactical: 100%
        drive:    100%
0h> wt s0 s1 s2
1 unit(s) need orders:
s3 Defender-4 (30.00, 18.00) W=1.00 CV=1.00 [###])))  NO ORDERS
0h> at s3 e0
All units have orders.
0h> r
17h =====[ COMBAT REPORT for coordinates (16.85, 23.86) ]=====
  Friendly CV x0.75, enemy CV x1.25

  Outcome   Unit           S-Dmg  H-Dmg
  -------   ----           -----  -----
  HULL-DMG  s3 Defender-4  1.0    0.2    SYS-DMG: shields: -25%
  SHLD-HIT  e0 Raider-A    0.7    0.0

17h Received message: PausedSimulation()
```
