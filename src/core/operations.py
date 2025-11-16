"""
Core Engine for Whale Proof Assistant

This module defines the fundamental data manipulation operations:
- Pattern matching
- Substitution
- Application reduction
"""

from .objects import Object,Term, Hole, Rew, Comp

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
        return False
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
        return Object(B.type, new_children, B.handle, B.repr)


def compose(A, B):
    """
    Compose two rules (match A's right with B's left)
    """
    if A.type != "Rew" or B.type != "Rew" or A.symbol != B.symbol:
        return None
    assignements = match(A.right, B.left)
    if assignements is not None:
        return Rew(A.left, A.symbol, apply(B.right, assignements))
    else:
        return None

def reduce(term):
    """
    Finds all the non-overlapping compositions in the term and applies the rule if possible.
    Returns the "1-step parallel" reduced term, or the original term if no reduction is possible.
    """
    if term.type == "Comp":
        attempt = compose(term.left, term.right)
        if attempt is not None:
            return attempt
        return term
    else:
        new_children = [reduce(child) for child in term.children]
        return Object(term.type, new_children, term.handle, term.repr)

def reduce_fully(term, max_steps=100):
    """
    Repeatedly applies reduce until no more reductions are possible.
    Returns the fully reduced term.
    """
    current = term
    for _ in range(max_steps):
        reduced = reduce(current)
        if reduced == current:
            raise ValueError("Max number of steps reached, reduction not finished")
        current = reduced
    return current
