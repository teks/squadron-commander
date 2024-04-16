PYTREK
======

Command a squadron of starships to protect a region of space. This is yet
another game in the tradition founded by Mike Mayfield in 1971:

https://en.wikipedia.org/wiki/Star_Trek_(1971_video_game)

The version I played the most as a kid, and referenced the most while designing
this one, was the terrific EGA Trek by Nels Anderson.

Unlike most trek games, in this version the raiders move and act on their own,
rather than remaining still, and instead of searching for them, one intercepts
them as they raid vulnerable space stations. Run `waves-of-raiders.py` to play
a demo scenario.

This game is not user-friendly; there is no tutorial. You're just going to have
to read documentation like an adult. See `HOWTOPLAY.md`.

Development
-----------

It is written in pure python (tested on python 3.11.5), with no dependencies
unless you want to run the test suite (see below). `waves-of-raiders.py`, being
a short script, is a good entry point for understanding the code and how to
write your own scenarios and other content such as custom ships.

`planning.txt` lists all the work not done and the great many bugs unfixed;
nevertheless I swear I've never worked for Bethesda.

To run the test suite:
1. `pip -r requirements.txt`
2. `PYTHONPATH=\`pwd\` pytest`
