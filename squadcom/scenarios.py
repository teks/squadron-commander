import dataclasses
import random
import string

from . import engine


@dataclasses.dataclass
class DefaultScenario(engine.EndlessScenario):
    include_enemies: bool=False
    include_colonies: bool=False

    def setup(self, initialize_simulation=True):
        for (d, p) in (('abel', (5, 5)),
                       ('baker', (35, 30)),
                       ('charlie', (60, 60)),
                       ('doug', (4, 58)),
                       ('alice', (7, 7))):
            self.simulation.populate(engine.FriendlyShip(d, engine.point(*p)))

        if self.include_enemies:
            for (d, p) in (('ukliss',  (20, 23)),
                           ('klaybeq', (32, 32)),
                           ('lowragh', (60, 53))):
                self.simulation.populate(engine.EnemyShip(d, engine.point(*p)))

        if self.include_colonies:
            for (d, p) in (('New Ceylon', (40, 12)),
                           ('Harmony',    (28, 56))):
                self.simulation.populate(engine.SpaceColony(d, engine.point(*p)))
        if initialize_simulation:
            self.simulation.initialize()
        return self.simulation


class WesternRaider(engine.EnemyShip):
    def retreats_from(self, side_cv_ratio):
        """Randomly determines if a ship retreats from battle.

        On retreat, warps away West
        """
        retreats = super().retreats_from(side_cv_ratio)
        if retreats:
            dest = self.point + engine.Point(-1, 0) # run one ly West
            self.order(engine.Order.MOVE, destination=dest)
            self.retreat_text = f"RETREATING TO ({dest.x:.2f}, {dest.y:.2f})"
        return retreats


@dataclasses.dataclass
class WavesOfRaiders(engine.Scenario):
    """Waves of raiders appear on the left, attacking the local colonies.

    Friendly colonies are placed randomly on the right half.
    If they are all destroyed, you lose.
    """

    def __post_init__(self):
        super().__post_init__()

    def spawn_enemies(self, enemies):
        for enemy in enemies:
            self.simulation.add_object(enemy)
            self.enemies.append(enemy)

    def setup(self, initialize_simulation=True):
        # TODO that we're double-tracking objects here and in simulation suggests
        #   that Simulation's API for getting at such objects isn't ideal
        # colonies on right side of map
        self.colonies = {
            engine.SpaceColony(d, engine.random_point(x_range=(32, engine.MAX_X)))
            for d in ('New Ceylon', 'Harmony', 'St. Alessia', 'LynxHab-41c')}

        # friendly squadron
        self.friendlies = {engine.FriendlyShip(f'Defender-{n}', engine.random_point())
                           for n in (1, 2, 3, 4)}

        for o in (*self.colonies, *self.friendlies):
            self.simulation.populate(o)

        self.enemies = []
        self.ticks_until_spawn = 100

        # set up enemy waves and spawn the first one
        self.enemy_waves = []
        raider_desig_iter = (f'Raider-{x}' for x in string.ascii_uppercase)
        for cnt in (2, 3, 4, 5): # four waves of increasing numbers of foes
            wave = [WesternRaider(next(raider_desig_iter), engine.random_point((1, 1)))
                    for _ in range(cnt)]
            self.enemy_waves.append(wave)

        self.spawn_enemies(self.enemy_waves.pop(0)) # spawn the first wave

        if initialize_simulation:
            self.simulation.initialize()

    def finish_tick(self) -> bool:
        # game is lost if all colonies lost
        if all(c.is_destroyed() for c in self.colonies):
            self.simulation.message(engine.ScenarioLossMessage())
            return True
        # game is won if all waves are defeated while any colonies remain
        if len(self.enemy_waves) == 0 and all(e.is_destroyed() for e in self.enemies):
            self.simulation.message(engine.ScenarioWinMessage())
            return True
        # game is lost if all friendlies lost while any enemies remain
        if all(f.is_destroyed() for f in self.friendlies):
            self.simulation.message(engine.ScenarioLossMessage())
            return True
        self.ticks_until_spawn -= 1
        if self.ticks_until_spawn == 0:
            self.ticks_until_spawn = 100
            if len(self.enemy_waves) > 0:
                self.spawn_enemies(self.enemy_waves.pop(0))
        return False
