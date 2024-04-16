

This would be good for a 3D game set in space.

The galactic coordinate system is based on MGRS: https://en.wikipedia.org/wiki/Military_Grid_Reference_System

It is rectilinear rather than polar. It is a nested system of blocks and
sub-blocks, which are mostly rectangular prisms.

The format is: `<sector>-<zone>-<area>`. Each part is multiple characters.
If one hyphen is present, the sector is assumed and the format is `<zone>-<area>`.
Characters used are 0-9 followed by A-Z, for 36 total values, ie, 'C' is 12.

* Sectors are two-dimensional rectangles and divide up the galaxy. The format
  is not specified here.
* Each sector has many zones arranged in a 3D grid. Each zone is represented by
  an XYZ triplet, such as 3WD.
* Squares are within zones and use the same XYZ format.

Thus each sector contains contain 46,656 zones, and each zone contains in turn
46,656 areas. It might be better to cut it down to 32x32x32 so a few letters
can be reserved, and let the math be an easier power of two.

