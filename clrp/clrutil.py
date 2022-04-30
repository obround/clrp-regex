import copy


class CLR1Item:
    """An CLR(1) item"""

    def __init__(self, lhs, rhs, lookahead, parsed_till):
        self.lhs = lhs
        self.rhs = rhs
        self.lookahead = lookahead
        self.parsed_till = parsed_till

    def __hash__(self):
        return hash(self.lhs) ^ hash(tuple(self.rhs)) ^ hash(
            tuple(self.lookahead)) ^ hash(self.parsed_till)

    def __eq__(self, other):
        return (self.lhs == other.lhs and self.rhs == other.rhs
                and self.lookahead == other.lookahead
                and self.parsed_till == other.parsed_till)

    def is_final_item(self):
        return self.parsed_till == len(self.rhs)

    def move_forward(self):
        transition = self.rhs[self.parsed_till]
        self.parsed_till += 1
        return transition

    def first_of(self, first_sets):
        if self.parsed_till + 1 <= len(self.rhs) - 1:
            first = copy.deepcopy(
                self.gen_following_items(self.parsed_till, self.rhs,
                                         self.lookahead, first_sets))
            if "" in first:
                if self.parsed_till + 1 > len(self.rhs) - 1:
                    first.add(self.lookahead)
            return list(first - {""})
        else:
            return self.lookahead

    def gen_following_items(self, lhs, alt, lookahead, first_sets):
        beta = alt[lhs + 1:]
        beta.extend(lookahead)
        for i, x in enumerate(beta):
            # if we don't find a nullable item, stop
            if "" not in first_sets[x]:
                beta = beta[:i + 1]
                break
        first = set()
        for symbol in beta:
            first |= first_sets[symbol]
        return first

    def get_neighbor(self):
        return self.rhs[self.parsed_till]

    def make(self):
        return f"(\"{self.lhs}\", {self.rhs})"

    def dump(self):
        rhs_clone = copy.deepcopy(self.rhs)
        rhs_clone.insert(self.parsed_till, "•")
        rhs_dump = " ".join(rhs_clone)
        return f"{self.lhs} → [{rhs_dump}, {self.lookahead}]"


class CLR1State:
    """A state in an CLR(1) automaton"""

    def __init__(self, grammar, first_sets, items, state_id):
        self.grammar = grammar
        self.first_sets = first_sets
        self.items = items
        self.state_id = state_id
        self.compute_closure()

    def __eq__(self, other):
        # we need to convert them to set and then
        # comapre them because sets are unordered,
        # and lists are not
        return set(self.items) == set(other.items)

    def __hash__(self):
        return hash(self.state_id) ^ hash(tuple(self.items))

    def compute_closure(self):
        for item in self.items:
            if not item.is_final_item():
                if item.get_neighbor().islower():
                    for rhs in self.grammar[item.get_neighbor()]:
                        parsed_till = 0 if rhs != [""] else 1
                        new_item = CLR1Item(item.get_neighbor(), rhs,
                                            item.first_of(self.first_sets),
                                            parsed_till)
                        if new_item not in self.items:
                            self.items.append(new_item)

    def fork(self):
        items = []
        analyzed = {}
        # we are going to for the items into items
        # transitions and items for new states
        for item in copy.deepcopy(self.items):
            if not item.is_final_item():
                neighbor = item.get_neighbor()
                transition = item.move_forward()
                if neighbor in analyzed:
                    analyzed[neighbor].append(item)
                else:
                    # we aren't going to apply closure because
                    # when the item becomes a state, closure will
                    # be applied in __init__
                    item_set = [item]
                    analyzed[neighbor] = item_set
                    items.append((transition, item_set))
        return items

    def make(self):
        return self.state_id
