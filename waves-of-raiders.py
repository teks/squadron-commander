#!/usr/bin/env python
import trek
from trek import cli, scenarios

scenario = scenarios.WavesOfRaiders()
scenario.setup()
ui = cli.CmdUserInterface(scenario.simulation)
# print(ui.short_range_map(trek.point(32, 32), radius=32, scale=0.5))
ui.start()
