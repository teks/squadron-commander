#!/usr/bin/env python
import trek
from trek import cli, scenarios

scenario = scenarios.WavesOfRaiders()
scenario.setup()
ui = cli.CmdUserInterface(scenario.simulation)
ui.start()
