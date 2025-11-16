"""
Core Engine for Whale Proof Assistant

This module defines the fundamental data structures:
- Object (abstract syntax tree object)
- Term, Rew, Comp, Hole
"""



class Object:
    def __init__(self, type, children = [], handle = None, repr = None):
        self.type = type or "Object"
        self.children = children
        self.handle = handle # Name for terms, symbol for rules...
        self.repr = repr
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        if self.repr:
            return self.repr(self)
        else:
            if len(self.children) == 0:
                return self.handle
            return self.handle + "(" + ", ".join([str(child) for child in self.children]) + ")"

    def __eq__(self, other):
        return type(self) == type(other) and self.handle == other.handle and all([a1 == a2 for a1, a2 in zip(self.children, other.children)])

    def __getattr__(self, name):
        if name == "left" and len(self.children) == 2:
            return self.children[0]
        elif name == "right" and len(self.children) == 2:
            return self.children[1]
        elif name == "symbol":
            return self.handle
        else:
            raise AttributeError(f"Object has no attribute {name}")

class Term(Object):
    def __init__(self, name, arguments = []):
        super().__init__("Term", arguments, name)

class Rew(Object):
    def __init__(self, left, symbol, right):
        super().__init__("Rew", [left, right], symbol, 
        lambda self: str(self.children[0]) + " " + self.handle + " " + str(self.children[1]))

class Comp(Object):
    def __init__(self, left, right):
        super().__init__("Comp", [left, right], None,
        lambda self: str(self.children[0]) + " | " + str(self.children[1]))

class Hole(Object):
    def __init__(self, name):
        super().__init__("Hole", [], name, 
        lambda self: "[" + self.handle + "]")