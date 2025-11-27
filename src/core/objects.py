"""
Core Engine for Whale Proof Assistant

This module defines the fundamental data structures:
- Object (abstract syntax tree object)
- Term, Rew, Comp, Hole
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional, Callable, Any, Dict


@dataclass(frozen=True, slots=True, eq=False)
class Object:
    type: str
    children: Tuple['Object', ...]
    handle: Optional[str] = None
    repr_func: Optional[Callable] = None
    data: Dict[str, Any] = field(default_factory=dict)  # For custom object types to store additional data

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        if self.repr_func:
            return self.repr_func(self)
        else:
            if len(self.children) == 0:
                return self.handle
            return self.handle + "(" + ", ".join([str(child) for child in self.children]) + ")"

    def __eq__(self, other: object) -> bool:
        """Equality based on type, handle, and children (excluding repr_func and data)."""
        if not isinstance(other, Object):
            return False
        return (self.type == other.type and
                self.handle == other.handle and
                self.children == other.children)

    def __hash__(self) -> int:
        """Hash based on type, handle, and children."""
        return hash((self.type, self.handle, self.children))

    @property
    def left(self) -> 'Object':
        if len(self.children) == 2:
            return self.children[0]
        raise AttributeError("Object does not have left attribute")

    @property
    def right(self) -> 'Object':
        if len(self.children) == 2:
            return self.children[1]
        raise AttributeError("Object does not have right attribute")

    @property
    def symbol(self) -> Optional[str]:
        return self.handle

def Term(name: str, arguments: Tuple[Object, ...] = ()) -> Object:
    """Creates a term object."""
    if not isinstance(arguments, tuple):
        arguments = tuple(arguments)
    return Object("Term", arguments, name)

def Rew(left: Object, symbol: str, right: Object) -> Object:
    """Creates a rewriting rule object."""
    return Object("Rew", (left, right), symbol,
        lambda self: f"({str(self.children[0])} {self.handle} {str(self.children[1])})")

def Comp(left: Object, right: Object) -> Object:
    """Creates a composition object."""
    return Object("Comp", (left, right), None,
        lambda self: f"({str(self.children[0])} | {str(self.children[1])})")

def Hole(name: str) -> Object:
    """Creates a hole (pattern variable) object."""
    return Object("Hole", (), name,
        lambda self: "[" + self.handle + "]")

def identify(A: Object, rule: str) -> Object:
    """Creates an identity rewrite rule for an object."""
    return Rew(A, rule, A)

def get_child(obj: Object, indices: Tuple[int, ...]) -> Optional[Object]:
    """
    Navigate to a child using a sequence of indices.
    > get_child(parent, ())  # Returns parent
    >get_child(parent, (1, 1))  # Returns second child's second child
    """
    current = obj
    try:
        for index in indices:
            if index < 0 or index >= len(current.children):
                return None
            current = current.children[index]
        return current
    except (IndexError, AttributeError, TypeError):
        return None