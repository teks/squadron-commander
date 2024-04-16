import cmd

import trek

class CLI(cmd.Cmd):
    def do_echo(self, arg):
        print(f"Echoing: '{arg}'")

    def do_EOF(self, _):
        return self.do_quit(_)

    def do_quit(self, _):
        print("Quitting!")
        return True


# maybe not here in the long run
if __name__ == '__main__':
    cli = CLI()
    cli.cmdloop()