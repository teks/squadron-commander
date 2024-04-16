#!/usr/bin/env python
import squadcom
from squadcom import cli, scenarios

scenario = scenarios.WavesOfRaiders()
scenario.setup()
ui = cli.CmdUserInterface(scenario.simulation)
ui.start()
