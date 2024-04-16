import cmd
import pprint
import collections
import string

import trek

class CLI(cmd.Cmd):
    _cmd_ui = None # set later; just doing this to make pycharm less wrong

    def do_debug(self, _):
        import pdb
        pdb.set_trace()

    def do_map(self, arg):
        x, y = arg.split()
        center = trek.point(int(x), int(y))
        map_str = self._cmd_ui.short_range_map(center)
        print(map_str)

    def do_aomap(self, arg):
        map_str = self._cmd_ui.long_range_map()
        print(map_str)

    def do_move(self, arg):
        # TODO probably need standard argument parsing function
        #   that has standard error reporting etc
        #   ship_desig, destination, speed = self._cmd_ui.parse(arg,
        #       parse.SHIP_DESIG, parse.POINT, float)
        try:
            ship_desig, *rest = arg.split()
            destination = trek.point(int(rest[0]), int(rest[1]))
        except Exception as e:
            print(f"Invalid command: {e}")
            return
        self._cmd_ui.move_ship(ship_desig, destination)

    def do_run(self, arg):
        self._cmd_ui.run()

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
        self.label_prefixes = {
            trek.Ship: '^',
            # TODO enemies
            # TODO stars
        }
        # keep track of iteration of spaceborne object label usage
        label_chars = string.digits + string.ascii_uppercase
        self.label_iterators = {
            trek.Ship: iter(label_chars),
            # TODO add in:
            # '!': iter(label_chars),
            # '^': iter(label_chars),
        }
        # set labels for the objects in the simulation
        for o in sorted(simulation.objects(), key=lambda o: o.designation):
            self.set_ui_label(o)

    def start(self):
        return self.cli.cmdloop()

    def run(self, duration=24):
        try:
            self.simulation.run(duration)
        except self.simulation.NotReadyToRun as e:
            print("Not ready to run; do all ships have orders?")

    def short_range_map(self, center_point, radius=8):
        """Returns the map for a given bounding box."""
        cells = collections.defaultdict(list)
        for o in self.simulation.objects():
            # conveniently, round() returns an integer
            grid_point = trek.point(round(o.point.x), round(o.point.y))
            cells[grid_point].append(o)
        s = pprint.pformat(cells) + '\n' # debugging output
        # set bounding box including bounds-check for attempting to show territory outside the map
        lower_left = trek.point(max(1, center_point.x - radius), max(1, center_point.y - radius))
        upper_right = trek.point(min(trek.MAX_X, center_point.x + radius),
                                 min(trek.MAX_Y, center_point.y + radius))
        rows = []
        for y in range(lower_left.y, upper_right.y + 1):
            row = f'{y:2} ' # row label
            for x in range(lower_left.x, upper_right.x + 1):
                current_point = trek.point(x, y)
                if current_point in cells:
                    row += self.cell_string(cells[current_point])
                else:
                    row += '. '
            rows.append(row)
        s += '\n'.join(reversed(rows))
        # column labels in bottom row, but need to be spaced out
        s += '\n  ' + ''.join([f'  {c:2}' for c in range(lower_left.x + 1, upper_right.x + 1, 2)])
        return s

    def long_range_map(self):
        """Return trek-style map of entire simulation."""
        zones = collections.defaultdict(list)
        for o in self.simulation.objects():
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

    def set_ui_label(self, obj):
        """Attach a unique UX label [0-9A-Z] to an object, then return that label."""
        cls = obj.__class__
        obj._ui_label = self.label_prefixes[cls] + next(self.label_iterators[cls])
        return obj._ui_label

    def cell_string(self, contents):
        """Emits a string to describe a single grid cell."""
        # TODO Natural phenomena (ie a star) aren't included in the count.
        #   so if only one artificial object is present, its shown as eg ^T.
        #   perhaps ';' for multiple contacts which includes natural phenomena eg: ;7
        # :7  multiple contacts; in this case 7 contacts
        if (object_cnt := len(contents)) > 1:
            return f':{object_cnt}'
        return contents[0]._ui_label

    def get_object(self, identifying_string):
        """Returns the object with the given UI label or else the object's designator."""
        for o in self.simulation.objects():
            if o._ui_label == identifying_string:
                return o
        try:
            return next(o for o in self.simulation.objects() if o.designation == identifying_string)
        except StopIteration:
            raise ValueError(f"Object '{identifying_string}' not found.")

    def move_ship(self, ship_desig, destination):
        ship = self.get_object(ship_desig)
        ship.order(trek.Ship.Order.MOVE, destination=destination)
        self.idle_ship_check()

    def idle_ship_check(self):
        idle_ships = self.simulation.idle_ships()
        if len(idle_ships) == 0:
            print("All ships have their orders.")
        else:
            print(f"{len(idle_ships)} ships have no orders.")

    def message(self, message):
        match message:
            # not a real instantiation; the match syntax is gross:
            case trek.ArriveMessage():
                m = f"ARRIVAL: {message.ship.designation} has arrived at {message.ship.point}."
            case _:
                m = f"Received message: {message}"
        print(m)
