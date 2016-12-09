

class Turnstile:
    """
    ┌── ((locked)) <──┐
    │                 │
    │                 │
    │                 │ push()
    │ coin()          │
    │                 │
    │                 │
    └──> (unlocked) ──┘
    """


    def __init__(self):
        self.state = 'locked'
        self.coins = 0

    def coin(self):
        self.state = 'unlocked'
        self.coins += 1

    def push(self):
        self.state = 'locked'

