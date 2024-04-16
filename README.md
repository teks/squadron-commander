Basically just the old 'trek' game for Unix & DOS, but with multiple ships
under your command.

There's no useful entry point atm; use a script eg:

```
import trek
from trek import cli

simulation = trek.default_scenario(enemies=True, space_colonies=True)
ui = cli.CmdUserInterface(simulation)
print(ui.short_range_map(trek.point(32, 32), radius=32, scale=0.5))
simulation.initialize()
ui.start()
```

To run the test suite:
1. `pip -r requirements.txt`
2. `PYTHONPATH=\`pwd\` pytest`
