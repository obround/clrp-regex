from .parser import Lexer, Parser
from .ast import (Basic, Alt,
                  Concat, ZeroOrMore,
                  OneOrMore, ZeroOrOne,
                  Wildcard, PositiveSet,
                  NegativeSet)
from .util import State, Match


class RegularExpression:
    """A regular expression"""

    def __init__(self, regex):
        self.pos = 1
        self.basic_nodes = {}
        self.states = []
        self.alphabet = set()
        self.lexer = Lexer()
        self.parser = Parser({
            "regex": self.regex,
            "alt": self.alt,
            "basic": self.basic,
            "reserved": self.reserved,
            "concat": self.concat,
            "atom": self.atom,
            "zero_or_more": self.zero_or_more,
            "one_or_more": self.one_or_more,
            "zero_or_one": self.zero_or_one,
            "group": self.group,
            "escape_char": self.escape_char,
            "wildcard": self.wildcard,
            "char": self.char,
            "set_item": self.set_item,
            "set_items": self.set_items,
            "positive_set": self.positive_set
        })
        self.ast = self.parser.parse(self.lexer.lex(f"({regex})#"))[0]
        # the initial state is the firstpos of the root of the
        # syntax tree (in this case, 'self.ast' is the root node)
        self.initial_state = State(self.ast.firstpos, 0)
        # the location where '#' is marks the final state
        # (the last node in basic nodes)
        self.final_state = len(self.basic_nodes)
        self.build_states()
        self.states.sort()

    def build_states(self):
        state_id = 1
        unmarked_states = [self.initial_state]
        while unmarked_states:
            state = unmarked_states.pop()
            self.states.append(state)
            for letter in self.alphabet:
                # the composition of the new state
                composition = set()
                for i in state.composition:
                    if self.basic_nodes[i].value.match == letter:
                        composition |= self.basic_nodes[i].followpos
                if composition:
                    new_state = State(composition, state_id)
                    # we don't want duplicate states
                    if new_state not in self.states:
                        unmarked_states.append(new_state)
                        state_id += 1
                    else:
                        # if the state already is in 'self.states',
                        # set 'new_state' to that states
                        new_state = self.states[self.states.index(new_state)]
                    # add the transition upon 'letter' to the new state
                    state.transitions[letter] = new_state

    def findall(self, string):
        state = self.initial_state
        matches = []
        last_pos = 0
        for pos, char in enumerate(string, 1):
            try:
                state = state.transitions[char]
            except KeyError:
                if self.final_state in state.composition and last_pos != pos - 1:
                    matches.append(Match((last_pos, pos - 1),
                                         string[last_pos: pos - 1]))
                state = self.initial_state
                last_pos = pos
        if self.final_state in state.composition and last_pos != pos:
            matches.append(Match((last_pos, pos), string[last_pos: pos]))
        return matches

    def finditer(self, string):
        state = self.initial_state
        last_pos = 0
        for pos, char in enumerate(string, 1):
            try:
                state = state.transitions[char]
            except KeyError:
                if self.final_state in state.composition and last_pos != pos - 1:
                    yield Match((last_pos, pos - 1), string[last_pos: pos - 1])
                state = self.initial_state
                last_pos = pos
        if self.final_state in state.composition and last_pos != pos:
            yield Match((last_pos, pos), string[last_pos: pos])

    def fullmatch(self, string):
        state = self.initial_state
        matches = []
        for char in enumerate(string, 1):
            try:
                state = state.transitions[char]
            except KeyError:
                return None
        if self.final_state in state.composition:
            matches.append(Match((0, len(string)), string))
        return matches

    def check(self, string):
        state = self.initial_state
        for char in string:
            try:
                state = state.transitions[char]
            except KeyError:
                return False
        if self.final_state in state.composition:
            return True

    def dump_states(self):
        dump = ""
        for state in self.states:
            dump += state.dump()
            dump += "\n"
        return dump[:-2]

    def regex(self, p):
        return p[0]

    def basic(self, p):
        return p[0]

    def reserved(self, p):
        return p[0]

    def atom(self, p):
        return p[0]

    def alt(self, p):
        return Alt(p[0], p[2])

    def concat(self, p):
        return Concat(p[0], p[1])

    def zero_or_more(self, p):
        return ZeroOrMore(p[0])

    def one_or_more(self, p):
        return OneOrMore(p[0])

    def zero_or_one(self, p):
        return ZeroOrOne(p[0])

    def group(self, p):
        return p[1]

    def positive_set(self, p):
        positive_set_node = PositiveSet(p[1], self.pos)
        self.pos = positive_set_node.pos
        self.alphabet |= positive_set_node.alphabet
        self.basic_nodes.update(positive_set_node.basic_nodes)
        return positive_set_node

    def negative_set(self, p):
        negative_set_node = NegativeSet(p[1], self.pos)
        self.pos = negative_set_node.pos
        self.alphabet |= negative_set_node.alphabet
        self.basic_nodes.update(negative_set_node.basic_nodes)
        return negative_set_node

    def set_item(self, p):
        if len(p) == 3:
            return (p[0], p[2])
        return p

    def set_items(self, p):
        return p

    def escape_char(self, p):
        if p[1].match == "s":
            p[1].match = " "
        elif p[1].match == "r":
            p[1].match = "\r"
        elif p[1].match == "n":
            p[1].match = "\n"
        return p[1]

    def wildcard(self, p):
        wildcard_node = Wildcard(self.pos)
        self.pos = wildcard_node.pos
        self.alphabet |= wildcard_node.alphabet
        self.basic_nodes.update(wildcard_node.basic_nodes)
        return wildcard_node

    def char(self, p):
        char_node = Basic(p[0], self.pos)
        # will be used while building the dfa states
        self.basic_nodes[self.pos] = char_node
        self.alphabet.add(p[0].match)
        self.pos += 1
        return char_node
