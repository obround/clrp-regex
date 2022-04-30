class State:
    """A state in the DFA"""

    def __init__(self, composition, state_id):
        # the nfa states this state is composed of
        # note that the nfa is not explicitly built
        self.composition = composition
        self.state_id = state_id
        self.transitions = {}

    def __eq__(self, other):
        return self.composition == other.composition
    
    def __lt__(self, other):
        # so that we can sort the list of states
        return self.state_id < other.state_id

    def dump(self):
        dump = f"state {self.composition}:\n----------------\n"
        for letter, to_state in self.transitions.items():
            dump += f"goto state {to_state.composition} upon '{letter}'\n"
        return dump


class Match:
    """A regex match"""

    def __init__(self, span, match):
        self.span = span
        self.match = match
    
    def __repr__(self):
        return f"<regex.Match <span={self.span}, match=\"{self.match}\">>"
