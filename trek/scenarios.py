import dataclasses
import random
import string

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


@dataclasses.dataclass
class WavesOfRaiders(trek.Scenario):
    """Waves of raiders appear on the left, attacking the local colonies.

    Friendly colonies are placed randomly on the right half.
    If they are all destroyed, you lose.
    """

    def __post_init__(self):
        super().__post_init__()

    def wave_generator(self):
        # four waves of increasing numbers of foes
        raider_desig_iter = (f'Raider-{x}' for x in string.ascii_uppercase)
        for cnt in (2, 3, 4, 5):
            wave = [trek.EnemyShip(next(raider_desig_iter), trek.random_point((1, 1)))
                    for _ in range(cnt)]
            for enemy in wave:
                self.simulation.add_object(enemy)
                self.enemies.append(enemy)
            yield True

    def setup(self, initialize_simulation=True):
        # TODO that we're double-tracking objects here and in simulation suggests
        #   that Simulation's API for getting at such objects isn't ideal
        # colonies on right side of map
        self.colonies = {
            trek.SpaceColony(d, trek.random_point(x_range=(32, trek.MAX_X)))
            for d in ('New Ceylon', 'Harmony', 'St. Alessia', 'LynxHab-41c')}

        # friendly squadron
        self.friendlies = {trek.FriendlyShip(f'Defender-{n}', trek.random_point())
                           for n in (1, 2, 3, 4)}

        for o in (*self.colonies, *self.friendlies):
            self.simulation.add_object(o)

        # set up enemy waves and spawn the first one
        self.enemies = []
        self.ticks_until_spawn = 100
        self._wave_iter = self.wave_generator()
        next(self._wave_iter)

        if initialize_simulation:
            self.simulation.initialize()

    def finish_tick(self) -> bool:
        if all(c.is_destroyed() for c in self.colonies):
            self.simulation.message(trek.ScenarioLossMessage())
            return True
        if all(f.is_destroyed() for f in self.friendlies):
            self.simulation.message(trek.ScenarioLossMessage())
            return True
        self.ticks_until_spawn -= 1
        if self.ticks_until_spawn == 0:
            self.ticks_until_spawn = 100
            rv = next(self._wave_iter, None)
            if rv is None and all(e.is_destroyed() for e in self.enemies):
                self.simulation.message(trek.ScenarioWinMessage())
                return True
        return False
