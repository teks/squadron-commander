from .engine import (
    MAX_X, MAX_Y, # constants that should be settings
    Point, point, # geometry
    SpaceborneObject, ArtificialObject, # base classes for objects floating in space
    Side, Controller, CombatSide, # organize objects into groups
    Order, # give objects behaviors
    SpaceColony, Ship, FriendlyShip, EnemyShip, # specific spaceborne object types
    # message-passing among all the objects
    Message, PausedSimulation, ArriveMessage, SpawnMessage, DestroyedObjectMessage,
        ChosenNewTarget, CombatReport, CompletedRepairsMessage,
    UserInterface, # empty stub for providing UX
    Scenario, # game setup & end-of-game checking
    EndlessScenario, # empty scenario used as a default by Simulation
    Simulation, # contains most of the above and runs the simulation
    default_scenario, # needs to come out now that there's a class ---v
)

from .scenarios import (
    # a few friendly and enemy ships and some colonues, useful for debugging
    DefaultScenario,
)
