import copy
from .actions import Shift, Reduce, Accept
from .clrutil import CLR1Item, CLR1State
from .codegen import TEMPLATE


class ParseError(Exception):
    pass


class TransitionTable(dict):
    """Similar to collections.defaultdict, but only for dicts"""

    def __init__(self):
        super().__init__(self)

    def __getitem__(self, k):
        if k not in self:
            self[k] = dict()
        return super().__getitem__(k)


class CLR1Parser:
    """An CLR(1) parser"""

    def __init__(self, grammar, start="start", dispatch=None):
        self.production_numbers = {(".start", (start)): -1}
        self.grammar = self.build_grammar(grammar)
        self.start = start
        self.dispatch = dispatch
        self.state_id = 1
        self.table = {}
        self.first_sets = {}
        self.compute_first_sets()
        self.transitions = TransitionTable()
        self.states = [
            CLR1State(self.grammar, self.first_sets,
                      [CLR1Item(".start", [self.start], ["$"], 0)], 0)
        ]
        self.compute_states(self.states[-1])
        self.compute_table()

    def build_grammar(self, grammar):
        built = {}
        i = 0
        # we iterate over a the string's lines without
        # any trailing newlines
        for _line in grammar.replace("\n", "").split("."):
            line = _line.strip()
            if line.split():
                nterm, prods = line.split(":")
                built[nterm.strip()] = []
                for alt in prods.split("|"):
                    # put the alts split by their spaces in unless
                    # we find @ (epsilon) (then we make it "")
                    production = [
                        item.strip() if item.strip() != "@" else ""
                        for item in alt.split()
                    ]
                    built[nterm.strip()].append(production)
                    self.production_numbers[(nterm, tuple(production))] = i
                    i += 1
        return built

    def compute_states(self, in_state):
        existing_states = set()
        # fork the states into transitions and item sets
        forks = in_state.fork()
        for fork in forks:
            (transition, items) = fork
            new_state = CLR1State(self.grammar, self.first_sets, items,
                                  self.state_id)
            self.state_id += 1
            for existing_state in self.states:
                if existing_state == new_state:
                    existing_states.add(existing_state)
                    new_state = existing_state
                    self.state_id -= 1
                    break
            else:
                self.states.append(new_state)
            # add the transition
            self.transitions[in_state][transition] = new_state

        # recursively build the other states
        for state in list(self.transitions[in_state].values()):
            if state not in existing_states:
                self.compute_states(state)

    def compute_first_sets(self):
        # we store the first sets in sets so
        # that there are no duplicate items
        for nterm, prods in self.grammar.items():
            for alt in prods:
                for item in alt:
                    if item.isupper():
                        self.first_sets[item] = {item}
            # first set of the non-terminals
            self.first_sets[nterm] = set()

        # here we use the iterative algorithm
        while True:
            changes = copy.deepcopy(self.first_sets)
            for nterm in self.grammar:
                for alt in self.grammar[nterm]:
                    # rule 1: if a → A α:
                    # first(a) = { a }
                    if alt[0].isupper() or alt[0] == "":
                        self.first_sets[nterm].add(alt[0])
                    elif alt[0].islower():
                        # rule 2: if a → B α:
                        # first(a) = first(b)
                        if "" not in self.first_sets[alt[0]]:
                            self.first_sets[nterm] |= self.first_sets[alt[0]]
                        else:
                            # rule 3: if a → B α (and ε ∈ B):
                            # first(a) = first(b)
                            alt_first_sets = set()
                            if len(alt) >= 2:
                                # get the first sets of α until first(αᵢ) ∉ ε
                                alt_first_sets |= self.first_sets[alt[1]]
                                for x in alt[2:]:
                                    if "" not in self.first_sets[x]:
                                        break
                                    alt_first_sets |= self.first_sets[x]
                            # remove ε ("" in this case) from the next item, and
                            # union it with the 'alt_first_sets'
                            self.first_sets[nterm] |= (
                                self.first_sets[alt[0]] -
                                {""}).union(alt_first_sets)
            # if we find that no changes were made to
            # the first sets (which means that we have
            # successfully calculated the first sets),
            # we return them
            if changes == self.first_sets:
                return self.first_sets

    def compute_table(self):
        for state in self.states:
            # we create the parsing table in two passes; first
            # we write the shifts then the reductions so that
            # we can catch shift-reduce conflicts

            # first pass
            for item in state.items:
                if not item.is_final_item():
                    neighbor = item.get_neighbor()
                    # if we find a terminal: shift
                    if neighbor.isupper():
                        self.table[state.state_id, neighbor] = Shift(
                            self.transitions[state][neighbor])
                    else:
                        # if we find a non-terminal: goto
                        self.table[state.
                                   state_id, neighbor] = self.transitions[
                                       state][neighbor].state_id
            # second pass
            for item in state.items:
                if item.is_final_item() and item.lhs != ".start":
                    # we don't want to reduce the start symbol;
                    # we want to accept it (else statement)
                    for la in item.lookahead:
                        # if we find a final item: reduce (and
                        # resolve any conflicts if present)
                        action = Reduce(item.lhs, item.rhs)
                        self.table[state.state_id, la] = self.resolve_conflict(
                            self.table.get((state.state_id, la)), action)
                elif item.is_final_item():
                    self.table[state.state_id, "$"] = Accept()

    def resolve_conflict(self, old_action, new_action):
        if old_action is None:
            return new_action

        # shift-reduce conflict detected
        if isinstance(old_action, Shift):
            # shift wins over reduce by default
            print("handling shift-reduce conflict in favor of shift")
            return old_action
        # reduce-reduce conflict detected
        elif isinstance(old_action, Reduce):
            # first production listed in chosen
            print(
                "handling reduce-reduce conflict in favor of first production listed"
            )
            old_action_loc = self.production_numbers[(old_action.lhs,
                                                      tuple(old_action.rhs))]
            new_action_loc = self.production_numbers[(new_action.lhs,
                                                      tuple(new_action.rhs))]
            if old_action_loc > new_action_loc:
                return new_action
            else:
                return old_action

    def parse(self, tokens, build_tree=False):
        if not build_tree and not self.dispatch:
            raise ValueError("dispatch required to build ast")
        # add the '$' to mark EOF
        tokens.append("$")
        index = 0
        stack = [0]
        node_stack = []

        cur_token = tokens[index]
        while True:
            try:
                move = self.table[stack[-1], cur_token]
            except KeyError as e:
                raise ParseError(f"no transition in table for {e}")
            if isinstance(move, Shift):
                # shift a token on the stack
                stack.append(cur_token)
                node_stack.append(cur_token)
                stack.append(move.transition_state.state_id)

                index += 1
                cur_token = tokens[index]

            elif isinstance(move, Reduce):
                if move.rhs != [""]:
                    # pop 2 * the amount of prods, and replace
                    # it with the prod's non-terminal
                    stack = stack[:-(2 * len(move.rhs))]
                    children = [
                        node_stack.pop() for _ in range(0, len(move.rhs))
                    ]
                    # get the node's children
                    if build_tree:
                        node_stack.append({move.lhs: list(reversed(children))})
                    else:
                        flat_children = list(self.flatten(children))
                        node_stack.append(self.dispatch[move.lhs](list(
                            reversed(flat_children))))
                else:
                    node_stack.append([])
                top = stack[-1]
                stack.append(move.lhs)
                try:
                    stack.append(self.table[top, move.lhs])
                except KeyError as e:
                    raise ParseError(f"no transition in table for {e}")

            elif isinstance(move, Accept):
                # if not all the tokens were seen before
                # we got the start symbol: error
                assert index == len(tokens) - 1, "garbage after parsed stream"
                # remove the $ an return the parse node_stack
                tokens.remove("$")
                return node_stack

    def format_tree(self, tree, level=0, inc=1):
        ret = ""
        if isinstance(tree, dict):
            for lhs, children in tree.items():
                ret += " " * level + lhs + "\n"
                ret += self.format_tree(children, level + inc)
        elif isinstance(tree, list):
            for item in tree:
                child = self.format_tree(
                    item, level + (inc if not isinstance(item, list) else 0))
                ret += child
        else:
            ret += " " * level + tree + "\n"
        return ret

    def codegen(self, out_file="parser.py"):
        parser = open(out_file, "w")
        dispatch_layout = ",".join(
            [f"{k}:{v}"
             for k, v in self.dispatch.items()]) if self.dispatch else ""
        parser.write(
            TEMPLATE.format(dispatch=dispatch_layout, table=self.make_table()))
        parser.close()

    def make_table(self):
        # make a string version of the table
        make = ""
        for k, v in self.table.items():
            make += f"{k}: {v.make() if not isinstance(v, int) else v},\n            "
        return make

    def dump_states(self):
        dump = ""
        for state in copy.deepcopy(self.states):
            dump += f"state {state.state_id}\n------------------\n"
            for item in state.items:
                # get the transition
                transition_to = str(
                    self.transitions[state][item.get_neighbor()].state_id
                ) + f" upon '{item.get_neighbor()}'" if not item.is_final_item(
                ) else "final item (no transition)"
                dump += f"{item.dump()} [goto: {transition_to}]"
                dump += "\n"
            dump += "\n"
        return dump

    def dump_table(self):
        dump = ""
        for k, v in self.table.items():
            dump += f"state {k[0]} on symbol {k[1]}: {v.dump() if not isinstance(v, int) else v}\n"
        return dump
