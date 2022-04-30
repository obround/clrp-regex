class Token:
    """A token"""

    def __init__(self, tag, match, pos):
        self.tag = tag
        self.match = match
        self.pos = pos

    def __eq__(self, other):
        return self.tag == other.tag and self.match == other.match and self.pos == other.pos


class Lexer:
    """A simple hand-written regex lexer"""

    def lex(self, regex):
        # reserve the maximum amount of space needed
        stream = [None] * len(regex)

        escape = False
        for i, char in enumerate(regex):
            if escape:
                stream[i] = Token("CHAR", char, i)
                escape = False
            elif char == "\\":
                stream[i] = Token("SLASH", "\\", i)
                escape = True
            elif char == "^":
                stream[i] = Token("NEGATE", "^", i)
            elif char == "(":
                stream[i] = Token("LPAREN", "(", i)
            elif char == ")":
                stream[i] = Token("RPAREN", ")", i)
            elif char == "[":
                stream[i] = Token("LBRACKET", "(", i)
            elif char == "]":
                stream[i] = Token("RBRACKET", ")", i)
            elif char == "*":
                stream[i] = Token("STAR", "*", i)
            elif char == "+":
                stream[i] = Token("PLUS", "+", i)
            elif char == "?":
                stream[i] = Token("OPT", "?", i)
            elif char == "|":
                stream[i] = Token("ALT", "|", i)
            elif char == ".":
                stream[i] = Token("DOT", ".", i)
            elif char == "-":
                stream[i] = Token("TO", "-", i)
            else:
                stream[i] = Token("CHAR", char, i)

        return stream
