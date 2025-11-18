"""
Core Engine for Whale Proof Assistant

This module defines the fundamental data manipulation operations:
- Pattern matching
- Substitution
- Application reduction
"""

from .objects import Object,Term, Hole, Rew, Comp, identify
from copy import deepcopy as copy

def match(A: Object, B: Object):
    """
    Find A against B.
    Returns a dictionary of assignments for the holes of B to match A, or None if no match is possible.
    """
    assignments = {}
    

    if B.type == "Hole":
        if B.handle in assignments:
            return assignments if assignments[B.handle] == A else None
        else:
            assignments[B.handle] = A
            return assignments

    if A.handle != B.handle or len(A.children) != len(B.children):
        return None
    for A_child, B_child in zip(A.children, B.children):
        found = match(A_child, B_child)
        if found is None:
            return None
        assignments.update(found)
    return assignments


def apply(B: Object, assignments: dict):
    """
    Applies assignments to a term with holes, filling in the holes.
    """
    if B.type == "Hole":
        if B.handle in assignments:
            return assignments[B.handle]
        else:
            return B
    else:
        new_children = [apply(child, assignments) for child in B.children]
        new_object = copy(B)
        new_object.children = new_children
        return new_object


def compose(A, B):
    """
    Compose two rules (match A's right with B's left)
    You can also compose an object with a rewriting (in that order), and get an object.
    """
    if B.type != "Rew" or (A.type == "Rew" and A.symbol != B.symbol):
        return None
    identified = False
    if A.type != "Rew":
        A = identify(A, B.symbol)
        identified = True
    assignements = match(A.right, B.left)
    if assignements is not None:
        result = Rew(A.left, A.symbol, apply(B.right, assignements))
        return result if not identified else result.right
    else:
        return None

def reduce_once(term):
    """
    Finds all the non-overlapping compositions in the term and applies the rule if possible.
    Returns the "1-step parallel" reduced term, or the original term if no reduction is possible.
    """
    if term.type == "Comp":
        attempt = compose(term.left, term.right)
        if attempt is not None:
            return attempt
    new_object = copy(term)
    new_children = [reduce_once(child) for child in term.children]
    new_object.children = new_children
    return new_object

def reduce(term, max_steps=100):
    """
    Repeatedly applies reduce until no more reductions are possible.
    Returns the fully reduced term.
    """
    current = term
    for _ in range(max_steps):
        reduced = reduce_once(current)
        if reduced == current:
            return current
        current = reduced
    raise ValueError("Max number of steps reached, reduction not finished")
