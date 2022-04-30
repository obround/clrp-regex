from .parser import Token


class Basic:
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos
        self.nullable = False
        self.firstpos = self.lastpos = {pos}
        self.children = {self}
        # will be expanded on by other nodes
        self.followpos = set()

    def __str__(self):
        return f"Basic(value=\"{self.value.match}\", nullable={self.nullable}, firstpos={self.firstpos}, lastpos={self.lastpos})"


class Alt:
    def __init__(self, first, second):
        self.first = first
        self.second = second
        self.nullable = self.first.nullable or self.second.nullable
        self.firstpos = self.first.firstpos | self.second.firstpos
        self.lastpos = self.first.lastpos | self.second.lastpos
        self.children = self.first.children | self.second.children

    def __str__(self):
        return f"Alt(nullable={self.nullable}, firstpos={self.firstpos}, lastpos={self.lastpos}, first={str(self.first)}, second={str(self.second)})"


class Wildcard:
    def __init__(self, pos):
        self.nullable = False
        self.pos = pos
        self.children = set()

        self.alphabet = set()
        self.basic_nodes = {}
        self.firstpos = set()
        self.lastpos = set()

        for i in range(255):
            node = Basic(
                Token("CHAR", chr(i), "?"), self.pos)
            self.basic_nodes[self.pos] = node
            self.alphabet.add(chr(i))
            self.pos += 1
            self.firstpos |= node.firstpos
            self.lastpos |= node.lastpos
            self.children.add(node)

    def __str__(self):
        return f"Wildcard(nullable=False, firstpos={self.firstpos}, lastpos={self.lastpos})"


class PositiveSet:
    def __init__(self, set_items, pos):
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()
        self.children = set()

        self.pos = pos
        self.alphabet = set()
        self.basic_nodes = {}

        flatten = lambda *n: (e for a in n
                              for e in (flatten(*a) if isinstance(a, list) else (a,)))
        for node in list(flatten(set_items)):
            if isinstance(node, tuple):
                for i in range(ord(node[0].value.match), ord(node[1].value.match) + 1):
                    char_node = Basic(Token("CHAR", chr(i), "?"), self.pos)
                    self.basic_nodes[self.pos] = char_node
                    self.alphabet.add(chr(i))
                    self.pos += 1
                    self.firstpos |= char_node.firstpos
                    self.lastpos |= char_node.lastpos
                    self.children.add(char_node)
            else:
                self.firstpos |= node.firstpos
                self.lastpos |= node.lastpos
                self.children.add(node)

    def __str__(self):
        return f"PositiveSet(nullable=False, firstpos={self.firstpos}, lastpos={self.lastpos})"


class NegativeSet:
    def __init__(self, set_items, pos):
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()
        self.children = set()

        self.pos = pos
        self.alphabet = set()
        self.basic_nodes = {}

        flatten = lambda *n: (e for a in n
                              for e in (flatten(*a) if isinstance(a, list) else (a,)))
        for node in list(flatten(set_items)):
            if isinstance(node, tuple):
                for i in range(ord(node[0].value.match), ord(node[1].value.match) + 1):
                    char_node = Basic(Token("CHAR", chr(i), "?"), self.pos)
                    self.basic_nodes[self.pos] = char_node
                    self.alphabet.add(chr(i))
                    self.pos += 1
                    self.firstpos |= char_node.firstpos
                    self.lastpos |= char_node.lastpos
                    self.children.add(char_node)
            else:
                self.firstpos |= node.firstpos
                self.lastpos |= node.lastpos
                self.children.add(node)

    def __str__(self):
        return f"PositiveSet(nullable=False, firstpos={self.firstpos}, lastpos={self.lastpos})"


class Concat:
    def __init__(self, first, second):
        self.first = first
        self.second = second
        self.nullable = self.first.nullable and self.second.nullable
        self.firstpos = self.first.firstpos | self.second.firstpos if self.first.nullable else self.first.firstpos
        self.lastpos = self.first.lastpos | self.second.lastpos if self.second.nullable else self.second.lastpos
        self.children = self.first.children | self.second.children

        for child in self.children:
            if child.pos in self.first.lastpos:
                child.followpos |= self.second.firstpos

    def __str__(self):
        return f"Concat(nullable={self.nullable}, firstpos={self.firstpos}, lastpos={self.lastpos}, first={str(self.first)}, second={str(self.second)})"


class ZeroOrMore:
    def __init__(self, node):
        self.node = node
        self.nullable = True
        self.firstpos = node.firstpos
        self.lastpos = node.lastpos
        self.children = self.node.children
        for child in self.children:
            if child.pos in self.lastpos:
                child.followpos |= self.firstpos

    def __str__(self):
        return f"ZeroOrMore(nullable=True, firstpos={self.firstpos}, lastpos={self.lastpos}, node={str(self.node)})"


class OneOrMore:
    def __init__(self, node):
        self.node = node
        self.nullable = node.nullable
        self.firstpos = node.firstpos
        self.lastpos = node.lastpos
        self.children = self.node.children
        for child in self.children:
            if child.pos in self.lastpos:
                child.followpos |= self.firstpos

    def __str__(self):
        return f"OneOrMore(nullable={self.nullable}, firstpos={self.firstpos}, lastpos={self.lastpos}, node={str(self.node)})"


class ZeroOrOne:
    def __init__(self, node):
        self.node = node
        self.nullable = True
        self.firstpos = node.firstpos
        self.lastpos = node.lastpos
        self.children = self.node.children

    def __str__(self):
        return f"OneOrMore(nullable=True, firstpos={self.firstpos}, lastpos={self.lastpos}, node={str(self.node)})"
