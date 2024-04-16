#!/usr/bin/env python

import argparse

import trek
from trek import cli

parser = argparse.ArgumentParser(
    description="PYTREK, a lo-fi turn based strategy game.",
)

parser.add_argument(
    '--scenario', default='dev', type=str,
    help="Specify a scenario."
)

# later pull this from a bank of scenario files
supported_scenarios = (
    'dev',
)

if __name__ == '__main__':
    args = parser.parse_args()
    s = args.scenario

    s = 'dev' if s is None else s # for now use 'dev' as a default scenario

    if s not in supported_scenarios:
        raise NotImplementedError(f"Unknown scenario '{s}'")

    simulation = trek.default_scenario()
    # TODO starting moves should be optional
    for ship in simulation.squadron:
        ship.order(ship.Order.MOVE, destination=trek.point(32, 32))
    ui = cli.CmdUserInterface(simulation)
    print(ui.short_range_map(trek.point(60, 60)))
    ui.start()