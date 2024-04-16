import dataclasses

from . import trek


@dataclasses.dataclass
class DefaultScenario(trek.EndlessScenario):
    include_enemies: bool=False
    include_colonies: bool=False

    def setup(self, initialize_simulation=True):
        for (d, p) in (('abel', (5, 5)),
                       ('baker', (35, 30)),
                       ('charlie', (60, 60)),
                       ('doug', (4, 58)),
                       ('alice', (7, 7))):
            self.simulation.add_object(trek.FriendlyShip(d, trek.point(*p)))

        if self.include_enemies:
            for (d, p) in (('ukliss',  (20, 23)),
                           ('klaybeq', (32, 32)),
                           ('lowragh', (60, 53))):
                self.simulation.add_object(trek.EnemyShip(d, trek.point(*p)))

        if self.include_colonies:
            for (d, p) in (('New Ceylon', (40, 12)),
                           ('Harmony',    (28, 56))):
                self.simulation.add_object(trek.SpaceColony(d, trek.point(*p)))
        if initialize_simulation:
            self.simulation.initialize()
        return self.simulation
