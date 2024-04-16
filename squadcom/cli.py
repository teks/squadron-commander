import dataclasses
import math
import cmd
import pprint
import collections
import string
import argparse
import itertools
import textwrap

import squadcom

MOVEMENT_MARKER_CHAR = '+'
class UI_LABEL_PREFIXES:
    friendly_controlled_ship = 's'
    enemy = 'e'
    friendly_space_colony = 'c'
    # TODO support a setting to control how it's visualized:
    #   (these labels are the originals: easier to view, harder to type)
    # friendly_controlled_ship = '^'
    # enemy = '!'
    # friendly_space_colony = '@'


# TODO enum?
# class EightCardinalDirections(enum.Enum):
#     EAST = 0 # but also stringifies to 'East'
cardinal_to_neighbor = {
    0: squadcom.Point(1, 0), # E
    1: squadcom.Point(1, 1), # NE
    2: squadcom.Point(0, 1), # N
    3: squadcom.Point(-1, 1), # NW
    4: squadcom.Point(-1, 0), # W
    5: squadcom.Point(-1, -1), # SW
    6: squadcom.Point(0, -1), # S
    7: squadcom.Point(1, -1), # SE
}


@dataclasses.dataclass
class SimpleTable:
    # TODO make headers optional then rewrite object_detail_display using SimpleTable
    headers: tuple
    field_templates: tuple
    rows: tuple
    column_separator = '  '
    header_separator = '-'

    def validate(self):
        w = len(self.headers)
        if w != len(self.field_templates) or any(w != len(r) for r in self.rows):
            raise ValueError("Inconsistent table width")

    def render_fields(self):
        rows = []
        for row in self.rows:
            rendered_row = tuple(self.field_templates[i].format(field_data)
                                 for (i, field_data) in enumerate(row))
            rows.append(rendered_row)
        return tuple(rows)

    def find_column_widths(self, rendered_fields):
        for i in range(len(self.headers)): # for each column
            max_field_width = max(len(row[i]) for row in rendered_fields)
            yield max(len(self.headers[i]), max_field_width)

    def render(self):
        """Yields each row of the table as a string in turn."""
        self.validate()
        rf = self.render_fields()
        column_widths = tuple(self.find_column_widths(rf))
        # format_spec can be specified dynamically:
        yield self.column_separator.join(
            '{:{w}}'.format(h, w=w) for (h, w) in zip(self.headers, column_widths))
        yield self.column_separator.join('{:{w}}'.format(self.header_separator * len(h), w=w)
                                         for (h, w) in zip(self.headers, column_widths))
        for row in rf:
            yield self.column_separator.join('{:{w}}'.format(field, w=w)
                                             for (field, w) in zip(row, column_widths))


def cli_header(blazon_count, text, blazon='='):
    """eg "===[ Combat Report ]===\n" """
    blazons = blazon * blazon_count
    return blazons + '[ ' + text + ' ]' + blazons

def combat_report_string(combat_report):
    indent = '  '
    fs, es = combat_report.friendly_side, combat_report.enemy_side
    st = SimpleTable(headers=('Outcome', 'Unit', 'S-Dmg', 'H-Dmg', ''),
                     field_templates=('{}', '{}', '{:.1f}', '{:.1f}', '{}'),
                     rows=(*combat_report_row_gen(fs), *combat_report_row_gen(es)))

    point = combat_report.point
    return '\n'.join([
        cli_header(5, f'COMBAT REPORT for coordinates ({point.x:.2f}, {point.y:.2f})'),
        indent + f'Friendly CV x{fs.cv_modifier:.2f}, enemy CV x{es.cv_modifier:.2f}\n',
        indent + f'\n{indent}'.join(st.render()) + '\n'
    ])
    return s

def percent_str(v: float):
    return f'{round(100.0 * v)}%'

def combat_report_row_gen(side):
    for u, (destroyed, shield_dmg, hull_dmg, sys_dmg) in side.outcomes.items():
        outcome = ('LOST' if destroyed else
                   'HULL-DMG' if hull_dmg > 0 else
                   'SHLD-HIT' if shield_dmg > 0 else '???')
        unit = getattr(u, '_ui_label', '??') + f' {u.designation}'
        notes = []
        if u in side.retreaters:
            notes.append(u.retreat_text)
        sys_dmg_str = ', '.join(f'{n}: {percent_str(-f)}' for n, f in sys_dmg.items() if f is not None)
        if sys_dmg_str:
            notes.append(f'SYS-DMG: {sys_dmg_str}')
        yield (outcome, unit, shield_dmg, hull_dmg, '. '.join(notes))


class PointAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, squadcom.point(*values))

# TODO it's an object_id or unit_id really, not just ships
SHIP_ID_ARG = ('ship_id', dict(type=str))
OBJECT_ID_ARG = ('object_id', dict(type=str))
MULTI_OBJECT_ID_ARG = ('object_id_list', dict(type=str, nargs='*'))
AT_LEAST_ONE_OBJECT_ID_ARG = ('object_id_list', dict(type=str, nargs='+'))

class CommandLineParser(argparse.ArgumentParser):
    """Needed because they let a bug into a release:

    https://github.com/python/cpython/issues/103498
    """
    def __init__(self, arguments, *args, **kwargs):
        # rely on `help COMMAND` instead vvvvv
        super().__init__(*args, add_help=False, **kwargs)
        for *args, kwargs in arguments:
            self.add_argument(*args, **kwargs)

    def error(self, message):
        raise ValueError(message)

    def exit(self, status=0, message=None):
        raise ValueError(
            "unexpected call to ArgumentParser.exit(status={status}, message='{message}')")

    def parse_line(self, line):
        try:
            # if needed, `import shlex` for better lexing (say, quoting of ship names)
            return self.parse_args(line.split())
        except Exception as e:
            print(e)

def generate_help_function(title, text):
    def f(_): # _ is cmd obj, see below
        print(title)
        print('=' * len(title))
        # for line in textwrap.fill(text): # <-- fill() does weird things for some reason
        for line in textwrap.wrap(text.strip()):
            print(line)

    return f

# TODO how to have multiple paragraphs? concatenates the two paras here:
OVERVIEW_TEXT = """
The game simulates a 2D version of spaceborne warfare on an interstellar scale,
similarly to Star Trek and other sci-fi. You are the commander of a squadron of
armed starships, tasked with achieving an objective based on the chosen scenario.

This text is a demo of the inline help system.
"""

class CLI(cmd.Cmd):
    _cmd_ui = None # set later; just doing this to make pycharm less wrong

    intro = (
        "Squadron Commander: A 2D interstellar wargame.\n"
        "   Inspired by the 'trek' games of the 70s and 80s\n"
        "   'help' or '?' to get started; try 'sm' to view the field of play.\n"
        "   Release version: " + squadcom.VERSION
    )

    doc_header = "Commands (type help <command>)"
    misc_header = "Other Help Topics (type help <topic>)"

    help_overview = generate_help_function("Overview", OVERVIEW_TEXT)

    def do_debug(self, _):
        """Drop into a pdb session."""
        ui = self._cmd_ui
        simulation = self._cmd_ui.simulation
        import pdb
        pdb.set_trace()

    map_parser = CommandLineParser(arguments=(
        ['centerpoint', dict(nargs=2, type=int, action=PointAction)],
        ['radius', dict(nargs='?', type=int, default=8)],
        ['scale', dict(nargs='?', type=float, default=1.0)],
    ))

    def do_map(self, arg):
        """`map` is currently disabled due to bugs. Try `sm`."""
        # map centerpoint_x centerpoint_y radius=8 scale=1.0
        print("This command has bugs and is disabled for the beta, sorry.")
        print("See `help sm` for info about the strategic map.")
        return
        # TODO scale > 1 does strange things eg map 32 32 10 2
        parsed_line = self.map_parser.parse_line(arg)
        if parsed_line is not None:
            map_str = self._cmd_ui.short_range_map(parsed_line.centerpoint,
                                                   parsed_line.radius, parsed_line.scale)
            print(map_str)

    def do_sm(self, _):
        """`sm` shows the strategic map, which is the entire field of play."""
        map_str = self._cmd_ui.short_range_map(squadcom.point(32, 32), 32, 0.5)
        print(map_str)

    # not needed given smap --^ resurrect later if there's a use for it
    # def do_aomap(self, arg):
    #     map_str = self._cmd_ui.long_range_map()
    #     print(map_str)

    object_id_list_parser = CommandLineParser(arguments=(MULTI_OBJECT_ID_ARG,))

    def do_ls(self, arg):
        """`ls` gives a one-line status display for any number of objects:

        0h> ls e0 s0
        e0 Raider-A   ( 1.00, 18.00) W=1.00 CV=1.00 [###])))  ATTACKING c0 Harmony (34.00, 19.00)
        s0 Defender-1 ( 4.00, 38.00) W=1.00 CV=1.00 [###])))  NO ORDERS

        With no arguments, lists all objects.
        """
        parsed_line = self.object_id_list_parser.parse_line(arg)
        if parsed_line is not None:
            self._cmd_ui.object_catalog(*parsed_line.object_id_list)

    def do_sh(self, arg):
        """`sh` shows the same output as `ls` but with more details added:

        0h> sh s0
        s0 Defender-1 (22.00, 60.00) W=1.00 CV=1.00 [###])))  MOVING to (25.00, 32.00)
            Base Repair Rate: 1% / hour        Morale: 0.00
            SYSTEM STATUS
                shields:  100%
                tactical: 100%
                drive:    100%
        """
        parsed_line = self.object_id_list_parser.parse_line(arg)
        if parsed_line is not None:
            self._cmd_ui.object_detail_display(*parsed_line.object_id_list)

    move_parser = CommandLineParser(arguments=(
        AT_LEAST_ONE_OBJECT_ID_ARG,
        ('destination', dict(nargs=2, type=float, action=PointAction)),
        # TODO add speed setting to move & attack cmd?
        # ('speed', dict(nargs='?', type=int, default=None)),
    ))

    def do_mv(self, arg):
        """`mv` orders any number of vessels to move to a destination point:

        15h> mv s2 15 25
        15h> mv s0 s1 s2 32 32
        """
        parsed_line = self.move_parser.parse_line(arg)
        if parsed_line is not None:
            # TODO hypervelocity goes in (also call it 'warpspeed'?)
            self._cmd_ui.move_ship(parsed_line.destination, *parsed_line.object_id_list)

    visit_parser = CommandLineParser(arguments=(
        AT_LEAST_ONE_OBJECT_ID_ARG,
        OBJECT_ID_ARG,
    ))

    def do_vs(self, arg):
        """`vs` orders vessels to visit the current location of any spaceborne object:

        Here, s2 and s3 are ordered to c0's location:
        20h> vs s2 s3 c0

        Note the target's location is only checked once, when the command is issued. To
        pursue an enemy in motion, see `help at`.
        """
        parsed_line = self.visit_parser.parse_line(arg)
        if parsed_line is not None:
            target = self._cmd_ui.get_object(parsed_line.object_id)
            if target is not None:
                self._cmd_ui.move_ship(target.point, *parsed_line.object_id_list)

    attack_parser = CommandLineParser(arguments=(
        AT_LEAST_ONE_OBJECT_ID_ARG,
        ('target_id', dict(type=str)),
    ))

    def do_at(self, arg):
        """`at` orders any number of vessels to intercept and attack a target:

        17h> at s0 s1 e0

        The target is pursued and attacked until it is destroyed or the
        interceptors are given new orders.
        """
        parsed_line = self.attack_parser.parse_line(arg)
        if parsed_line is not None:
            self._cmd_ui.attack(parsed_line.target_id, *parsed_line.object_id_list)

    wait_parser = CommandLineParser(arguments=(
        MULTI_OBJECT_ID_ARG,
        # TODO support timeouts in Order.IDLE params: ('duration', dict(type=int)),
    ))

    def do_wt(self, arg):
        """`wt` order any number of vessels to wait wherever they are.

        wt s0 s1

        They'll hold position until ordered to do otherwise.
        """
        parsed_line = self.wait_parser.parse_line(arg)
        if parsed_line is not None:
            self._cmd_ui.wait(*parsed_line.object_id_list)

    def set_prompt(self):
        self.prompt = f'{self._cmd_ui.simulation.clock}h> '

    @staticmethod
    def positive_int(s):
        if (i := int(s)) < 1:
            raise ValueError("Positive integers only")
        return i

    run_parser = CommandLineParser(arguments=(
        ('hour_count', dict(type=positive_int, nargs='?', default=24)),
    ))

    def do_r(self, arg):
        """`r` runs the simulation for the given number of ticks (default is 24):

        53h> r
        77h> r 12
        89h>

        All ships under your control must have orders or the simulation won't run.
        """
        parsed_line = self.run_parser.parse_line(arg)
        if parsed_line is not None:
            self._cmd_ui.run(parsed_line.hour_count)
            self.set_prompt()

    def do_EOF(self, _):
        """End-of-file characters quit the simulation."""
        print()
        return self.do_quit(_)

    def do_quit(self, _):
        """`quit` quits."""
        print("Quitting!")
        return True


class CmdUserInterface(squadcom.UserInterface):
    """UI for trek based on simple cmd.Cmd CLI."""
    class LabelIterators:
        def __init__(self):
            label_chars = string.digits + string.ascii_uppercase
            self.squadron = iter(label_chars)
            self.raiders = iter(label_chars)
            self.colonies = iter(label_chars)

    def __init__(self, simulation):
        # not sure I like this constant double-referencing, not sure how to avoid it
        self.simulation = simulation
        simulation.user_interface = self
        self.cli = CLI()
        self.cli._cmd_ui = self
        self.cli.set_prompt()
        # keep track of iteration of spaceborne object label usage
        self.label_iterators = self.LabelIterators()
        # set labels for the objects in the simulation
        for o in sorted(simulation.get_objects(), key=lambda o: o.designation):
            self.set_ui_label(o)

    def start(self):
        return self.cli.cmdloop()

    def point_str(self, point):
        return f"({point.x:5.2f}, {point.y:5.2f})"

    def run(self, duration=24):
        try:
            self.simulation.run(duration)
        except self.simulation.NotReadyToRun as e:
            print(f"Not ready to run; {len(e.args[0])} unit(s) need orders:")
            print('\n'.join(self.single_line_object_display(o) for o in e.args[0]))

    def object_catalog(self, *object_id_pile):
        lines = []
        for obj in self.object_generator(*object_id_pile):
            if obj is not None:
                line = self.single_line_object_display(obj)
                lines.append(line)
        print('\n'.join(lines))

    def single_line_object_display(self, obj):
        # TODO rewrite in terms of SimpleTable?
        line = f"{obj._ui_label} {obj.designation:10} {self.point_str(obj.point)}"
        if not isinstance(obj, squadcom.ArtificialObject):
            return line
        line += f" W={obj.speed:.2f} CV={obj.combat_value():.2f} {self.hull_and_shield_icon(obj)}"
        if obj.is_destroyed():
            return line

        order = obj.current_order
        if order == squadcom.Order.ATTACK:
            t = obj.current_order_params['target']
            line += f" ATTACKING {t._ui_label} {t.designation} {self.point_str(t.point)}"
        elif order == squadcom.Order.MOVE:
            line += " MOVING to " + self.point_str(obj.current_order_params['destination'])
        elif order == squadcom.Order.IDLE:
            line += '' if isinstance(obj, squadcom.SpaceColony) else " WAITING"
        elif order is None:
            line += ' NO ORDERS'
        else:
            raise ValueError(f"Unexpected order {order}")
        return line

    def hull_and_shield_icon(self, obj):
        if obj.is_destroyed():
            return "DESTROYED"
        # bin the hull status & shield status:
        hs = obj.hull_status()
        hull_str = ('   ' if hs < 0.25 else
                    '#  ' if hs < 0.5  else
                    '## ' if hs < 0.75 else '###')

        ss = obj.shields_status()
        shield_str = ('   ' if ss < 0.25 else
                      ')  ' if ss < 0.5  else
                      ')) ' if ss < 0.75 else ')))')

        return f"[{hull_str}]{shield_str} "

    # do_list should use this:
    def object_generator(self, *id_pile):
        """Yields each ID's object, or else all object if none specified."""
        if len(id_pile) > 0:
            yield from (self.get_object(o_id) for o_id in id_pile)
        else:
            yield from sorted(self.simulation.get_objects(), key=lambda o: o._ui_label)

    def object_detail_display(self, *object_id_pile):
        for o_id in self.object_generator(*object_id_pile):
            self.single_object_detail_display(o_id)

    def single_object_detail_display(self, o):
        if o is not None:
            text = '\n'.join([
                self.single_line_object_display(o),
                # add in current repair rate; have to pull out modifier from repair()
                f"    Base Repair Rate: {percent_str(o.repair_rate)} / hour"
                #     Morale: <in-universe statement from the captain here> (n)
                    f"        Morale: {o.morale:.2f}",
                # :9 is for vertical formatting:
                "    SYSTEM STATUS",
                *(f"        {name + ':':9} {percent_str(component.health)}"
                    for name, component in o.components.items())
            ])
            print(text)
            return text

    def add_movement_markers(self, layer, obj, scale):
        a, b = [obj.compute_move(ticks=n) for n in (1, 2)]
        if obj.point == a: # no movement, so no movement marker
            return
        # garauntee that the first marker doesn't overlap the object:
        if a is not None:
            rel_neighbor = cardinal_to_neighbor[obj.point.cardinal_direction_to(a)]
            cell = obj.point.grid_cell(scale) + rel_neighbor
            layer[cell].append(MOVEMENT_MARKER_CHAR)

        # for now the second marker goes wherever it goes
        # TODO this doesn't align with a in all cases
        # if b is not None:
        #     layer[b.grid_cell(scale)].append('x')

    def short_range_map(self, center_point, radius=8, scale=1.0):
        """Returns the map for a given bounding box."""
        obj_layer = collections.defaultdict(list)
        # for "graphics" that add info rather than show objects
        hud_layer = collections.defaultdict(list)
        for o in self.simulation.get_objects():
            obj_layer[o.point.grid_cell(scale)].append(o)
            self.add_movement_markers(hud_layer, o, scale)
        # set bounding box including bounds-check for attempting to show territory outside the map
        scaled_ceil = lambda v: math.ceil(scale * v)
        lower_left = squadcom.point(max(1, scaled_ceil(center_point.x - radius)),
                                    max(1, scaled_ceil(center_point.y - radius)))
        upper_right = squadcom.point(min(squadcom.MAX_X, scaled_ceil(center_point.x + radius)),
                                     min(squadcom.MAX_Y, scaled_ceil(center_point.y + radius)))
        rows = []
        group_label_iter = itertools.chain(iter(string.ascii_uppercase), itertools.repeat('?'))
        groups = [] # list of (label string, contents)
        for y in range(lower_left.y, upper_right.y + 1):
            row = f'{round(y / scale):2} ' if y % 2 == 0 else '   ' # label every other row

            # set the display string for each cell in the row
            for x in range(lower_left.x, upper_right.x + 1):
                p = squadcom.point(x, y)
                cell_contents = obj_layer[p]
                if len(cell_contents) == 1:
                    row += cell_contents[0]._ui_label
                elif len(cell_contents) > 1:
                    group_label = next(group_label_iter)
                    groups.append((group_label, p, cell_contents))
                    row += ':' + group_label
                else:
                    hud_contents = hud_layer[p]
                    if MOVEMENT_MARKER_CHAR in hud_contents:  # so far the only HUD item
                        row += MOVEMENT_MARKER_CHAR + ' '
                    else:
                        row += '. '  # empty cells get a dot as a kind of spatial grid marker
            rows.append(row)

        s = '\n'.join(reversed(rows))
        # column labels in bottom row, but need to be spaced out
        s += '\n  ' + ''.join([f'  {round(c / scale):2}'
                               for c in range(lower_left.x + 1, upper_right.x + 1, 2)])

        # group display after the map
        for label, p, contents in groups:
            s += (f'\n  [:{label}] Multiple contacts near {p.x / scale, p.y / scale}: '
                  + ', '.join(o._ui_label for o in contents))
        return s

    # smap sorta makes this unneeded, alas
    # def long_range_map(self):
    #     """Return trek-style map of entire simulation."""
    #     zones = collections.defaultdict(list)
    #     for o in self.simulation.get_objects():
    #         zones[o.point.zone()].append(o)
    #
    #     # generate the triple-digit displays & make grid
    #     rows = []
    #     for y in range(1, trek.MAX_ZONE_Y + 1):
    #         row = str(y)
    #         for x in range(1, trek.MAX_ZONE_X + 1):
    #             if trek.point(x, y) not in zones:
    #                 row += ' ...' # nothing in the zone
    #             else:
    #                 row += ' ' + self.zone_string(zones[trek.Point(x, y)])
    #         rows.append(row)
    #
    #     # row of column headers:
    #     text_map = ('\n'.join(reversed(rows)) + '\n '
    #                 + ''.join([f'  {c} ' for c in range(1, trek.MAX_ZONE_X + 1)]))
    #
    #     return "Got objects: " + pprint.pformat(zones) + '\n' + text_map

    def zone_string(self, contents):
        """Return a three-character string describing a zone.

        3-digit display per zone:
            * lead digit is enemy count
            * center digit is friendly count
            * right digit is star count
            * Period in any column: No information
        """
        ship_cnt = 0
        for o in contents:
            match o.side:
                case squadcom.Side.FRIENDLY:
                    ship_cnt += 1
                case _:
                    raise ValueError(f"Type for {o} isn't supported.")

        return f'0{ship_cnt}0'

    def set_ui_label(self, obj):
        """Attach a unique UX label [0-9A-Z] to an object, then return that label."""
        if isinstance(obj, squadcom.Ship):
            match (obj.side, obj.controller):
                case (squadcom.Side.FRIENDLY, squadcom.Controller.PLAYER):
                    obj._ui_label = UI_LABEL_PREFIXES.friendly_controlled_ship + next(
                        self.label_iterators.squadron)
                case (squadcom.Side.ENEMY, _):
                    obj._ui_label = UI_LABEL_PREFIXES.enemy + next(self.label_iterators.raiders)
                case _:
                    raise ValueError(
                        f"{obj} has unexpected (side, controller) of {obj.side, obj.controller}")
        elif isinstance(obj, squadcom.SpaceColony) and obj.side == squadcom.Side.FRIENDLY:
            obj._ui_label = UI_LABEL_PREFIXES.friendly_space_colony + next(self.label_iterators.colonies)
        else:
            raise ValueError(f"Couldn't assign UI label to {obj}")

        return obj._ui_label

    def get_object(self, identifying_string, side=None, controller=None):
        """Returns the object with the given UI label or else the object's designator."""
        # there's a small chance of a name collision between ui labels and designation,
        # so the least surprising thing is to always look in UI labels first.
        f = lambda: self.simulation.get_objects(side, controller)
        for o in f():
            if o._ui_label == identifying_string:
                return o
        try:
            return next(o for o in f() if o.designation == identifying_string)
        except StopIteration:
            print(f"Object '{identifying_string}' not found.")
            return None

    def move_ship(self, destination, *ship_id_pile):
        for ship_id in ship_id_pile:
            ship = self.get_object(ship_id, controller=squadcom.Controller.PLAYER)
            if ship is not None:
                ship.order(squadcom.Order.MOVE, destination=destination)
        self.check_orders()

    def attack(self, target_id: str, *ship_id_pile: tuple[str]):
        target = self.get_object(target_id, side=squadcom.Side.ENEMY)
        if target is None:
            return
        for ship_id in ship_id_pile:
            ship = self.get_object(ship_id, controller=squadcom.Controller.PLAYER)
            if ship is not None:
                ship.order(squadcom.Order.ATTACK, target=target)
        self.check_orders()

    def wait(self, *ship_id_pile: tuple[str]):
        if len(ship_id_pile) == 0:
            ships = self.simulation.objects_without_orders(controller=squadcom.Controller.PLAYER)
        else:
            ships = (self.get_object(sid, controller=squadcom.Controller.PLAYER) for sid in ship_id_pile)
        for ship in ships:
            if ship is not None:
                ship.order(squadcom.Order.IDLE)
        self.check_orders()

    def check_orders(self):
        """Confirm player-controlled vessels have orders."""
        units = self.simulation.objects_without_orders(squadcom.Side.FRIENDLY)
        if len(units) == 0:
            print("All units have orders.")
        else:
            print(f"{len(units)} unit(s) need orders:")
            for u in units:
                print(self.single_line_object_display(u))

    def message(self, message):
        m = f"{message.tick}h "
        match message:
            # not a real instantiation; the match syntax is gross:
            case squadcom.ArriveMessage():
                s = message.ship
                m += f"ARRIVAL: {s._ui_label} {s.designation} has arrived at {s.point}."
            case squadcom.SpawnMessage():
                self.set_ui_label(message.obj)
                m += "Object spawned: " + self.single_line_object_display(message.obj)
            case squadcom.CombatReport():
                m += combat_report_string(message)
            case _:
                m += f"Received message: {message}"
        print(m)
