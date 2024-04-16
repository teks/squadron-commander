import cmd
import pprint
import collections

import trek

class CLI(cmd.Cmd):
    def do_echo(self, arg):
        print(f"Echoing: '{arg}'")

    def do_aomap(self, arg):
        map_str = self._cmd_ui.long_range_map()
        print(map_str)

    def do_EOF(self, _):
        print()
        return self.do_quit(_)

    def do_quit(self, _):
        print("Quitting!")
        return True


class CmdUserInterface(trek.UserInterface):
    """UI for trek based on simple cmd.Cmd CLI."""

    def __init__(self, simulation):
        # not sure I like this constant double-referencing, not sure how to avoid it
        self.simulation = simulation
        simulation.user_interface = self
        self.cli = CLI()
        self.cli._cmd_ui = self

    def start(self):
        return self.cli.cmdloop()

    def long_range_map(self):
        """Return trek-style map of entire simulation."""
        zones = collections.defaultdict(list)
        for o in self.simulation.map.contents:
            zones[o.point.zone()].append(o)

        # generate the triple-digit displays & make grid
        rows = []
        for y in range(1, trek.MAX_ZONE_Y + 1):
            row = str(y)
            for x in range(1, trek.MAX_ZONE_X + 1):
                if trek.point(x, y) not in zones:
                    row += ' ...' # nothing in the zone
                else:
                    row += ' ' + self.zone_string(zones[trek.Point(x, y)])
            rows.append(row)

        # row of column headers:
        text_map = ('\n'.join(reversed(rows)) + '\n '
                    + ''.join([f'  {c} ' for c in range(1, trek.MAX_ZONE_X + 1)]))

        return "Got objects: " + pprint.pformat(zones) + '\n' + text_map

    def zone_string(self, contents):
        """Return a three-character string describing a zone.

        3-digit display per zone:
            * lead digit is enemy count
            * center digit is friendly count
            * right digit is star count
            * Period in any column: No information
        """
        # TODO try rewrite using patterns
        # https://docs.python.org/3/reference/compound_stmts.html#index-18
        ship_cnt = 0
        for o in contents:
            if isinstance(o, trek.Ship):
                ship_cnt += 1
            else:
                raise ValueError(f"Type for {o} isn't supported.")

        return f'0{ship_cnt}0'

    def local_map(self, center: trek.Point):
        """
        likely spacing is 2x1:
        . . .
        . . .
        . . .
        """

# maybe not here in the long run
if __name__ == '__main__':
    simulation = trek.default_scenario()
    ui = CmdUserInterface(simulation)
    ui.start()
