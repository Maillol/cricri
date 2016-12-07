

class Machine:
    """
      ┌──── A(x=0, y=0)────┐
      │                    │
      │ mth1()             │ mth2()
      V                    V
                 mth1()
    B(x=0, y=1) ─────────> C(x=0, y=2) ┐
                                       │
      │ mth2()             │ mth1()    │ mth2()   
      V                    V           │
                                       │
    D(x=1, y=0)      ┌──── E(x=1, y=1) │
                     │                 │
      │ mth1()       │ mth1()          │
      │              V                 │
      │                                │
      └───> F(x=1, y=2) <──────────────┘
    """

    states = {
        'A': ((0, 0), ('B', 'C')),
        'B': ((0, 1), ('C', 'D')),
        'C': ((0, 2), ('E', 'F')),
        'D': ((1, 0), ('F', None)),
        'E': ((1, 1), ('F', None)),
        'F': ((1, 2), (None, None))}

    def __init__(self):
        self.state = 'A'
        self.__apply_state()

    def __apply_state(self):
        self.x, self.y = self.states[self.state][0]

    def mth1(self):
        self.state = self.states[self.state][1][0]
        self.__apply_state()

    def mth2(self):
        self.state = self.states[self.state][1][1]
        self.__apply_state()


