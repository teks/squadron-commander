Basically just the old 'trek' game for Unix & DOS, but with multiple ships
under your command.

There's no useful entry point atm; use a script eg:

```
import trek
from trek import cli

simulation = trek.default_scenario()
ui = cli.CmdUserInterface(simulation)
print(ui.short_range_map(trek.point(60, 60)))
ui.start()
```

