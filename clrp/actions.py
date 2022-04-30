class Shift:
    """A shift move"""

    def __init__(self, transition_state):
        self.transition_state = transition_state

    def make(self):
        return f"Shift({self.transition_state.make()})"

    def dump(self):
        return f"shift and goto state {self.transition_state.state_id}"


class Reduce:
    """A reduce move"""

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def make(self):
        return f"Reduce(\"{self.lhs}\", {self.rhs})"

    def dump(self):
        rhs = " ".join([item for item in self.rhs])
        return f"reduce {self.lhs} → {rhs}"


class Accept:
    """An accept move"""

    def make(self):
        return f"Accept()"

    def dump(self):
        return "accept"
