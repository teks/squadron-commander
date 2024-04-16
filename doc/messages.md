UI object needs to be able to receive structured messages from the simulation
object when the simulation experiences events that the user would want to be
aware of:

```
ui.message(ui.ARRIVE, ship=some_ship, destination=some_point)
```

Or, make better use of methods:

```
ui.arrive_message(ship=some_ship, destination=some_point)
```

Which way should it be done? If the entire message is a value, ie:

```
m = ArriveMessage(ship, destination)
```

Then the message can be passed around as-needed. Right now the only
message-receiver is the UI object, but the simulation object may want
to receive Messages as well (and pass them through to the UI).

So a model implementation:

```
class Message:
    pass


class ArriveMessage(Message):
    def __init__(self, ship, destination):
        self.ship = ship
        self.destination = destination
```
