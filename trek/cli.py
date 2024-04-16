import cmd

import trek

class CLI(cmd.Cmd):
    def do_echo(self, arg):
        print(f"Echoing: '{arg}'")

    def do_aomap(self, arg):
        print(f"map")

    def do_EOF(self, _):
        print()
        return self.do_quit(_)

    def do_quit(self, _):
        print("Quitting!")
        return True


class CmdUserInterface(trek.UserInterface):
    """UI for trek based on simple cmd.Cmd CLI."""

    def __init__(self, simulation):
        self.simulation = simulation
        self.simulation.user_interface = self
        self.cli = CLI()

    def start(self):
        return self.cli.cmdloop()

    def long_range_map(self):
        """Return trek-style map of entire simulation.

        3-digit display per zone:
            * lead digit is enemy count
            * center digit is friendly count
            * right digit is star count

        ... ... ... ...
        ... ... ... ...
        ... ... ... ...
        ... ... ... ...
        """


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
