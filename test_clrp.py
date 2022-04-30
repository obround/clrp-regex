import clrp

if __name__ == "__main__":
    grammar = """\
        regex: alt | basic.
        alt: regex ALT basic.
        basic: concat | reserved.
        concat: basic reserved.
        reserved: zero_or_more | one_or_more | zero_or_one | atom.
        zero_or_more: atom STAR.
        one_or_more: atom PLUS.
        zero_or_one: atom OPT.
        atom: group | char | wildcard | positive_set | negative_set.
        wildcard: DOT.
        group: LPAREN regex RPAREN.
        char: CHAR | escape_char.
        positive_set: LBRACKET set_items RBRACKET.
        negative_set: LBRACKET NEGATE set_items RBRACKET.
        set_items: set_items set_item | set_item.
        set_item: char TO char | char.
        escape_char: SLASH CHAR.
    """
    #~ grammar = """\
    #~     a: A | b.
    #~     b: A.
    #~ """
    string = "CHAR CHAR PLUS CHAR"

    clr = clrp.CLR1Parser(grammar, start="regex")
    clr.codegen("parser_out.py")

    from parser_out import *

    parser = Parser()
    print(parser.format_tree(parser.parse(string.split(), True)))
