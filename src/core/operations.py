"""
Core Engine for Whale Proof Assistant

This module defines the fundamental data manipulation operations:
- Pattern matching
- Substitution
- Application reduction
"""

from typing import Optional, Dict, List
from .objects import Object,Term, Hole, Rew, Comp, identify

def prefix_holes(term: Object, prefix: str) -> Object:
    """
    Prefix all holes in a term with a given prefix.
    """
    if term.type == "Hole":
        return Hole(prefix + term.handle)
    else:
        return Object(term.type, tuple(prefix_holes(child, prefix) for child in term.children), term.handle, term.repr_func, term.data)

def unprefix_holes(term: Object, prefixes: List[str]) -> Object:
    """
    Unprefix all holes in a term with a given prefix.
    """
    if term.type == "Hole":
        handle = term.handle
        for prefix in prefixes:
            handle = handle.removeprefix(prefix)
        return Hole(handle)
    else:
        return Object(term.type, tuple(unprefix_holes(child, prefixes) for child in term.children), term.handle, term.repr_func, term.data)

def match_left(A: Object, B: Object) -> Optional[Dict[str, Object]]:
    """
    One-directional pattern matching: Find A against pattern B.
    Returns a dictionary of assignments for the holes of B to match A, or None if no match is possible.
    B is the pattern (may contain holes), A is the concrete term.
    """
    assignments = {}


    if B.type == "Hole":
        if B.handle in assignments:
            return assignments if assignments[B.handle] == A else None
        else:
            assignments[B.handle] = A
            return assignments

    # Check type compatibility
    if A.type != B.type:
        return None

    if A.handle != B.handle or len(A.children) != len(B.children):
        return None
    for A_child, B_child in zip(A.children, B.children):
        found = match_left(A_child, B_child)
        if found is None:
            return None
        assignments.update(found)
    return assignments


def match(A: Object, B: Object) -> Optional[Dict[str, Object]]:
    """
    Bidirectional syntactic unification of A and B.
    Returns a dictionary of assignments for holes in both A and B such that
    when applied to both terms, they become identical. Returns None if unification fails.
    Assumes terms have no common holes (no conflict resolution needed).
    """
    assignments = {}


    # If B is a hole, assign it to A
    if B.type == "Hole":
        if B.handle in assignments:
            return assignments if assignments[B.handle] == A else None
        else:
            assignments[B.handle] = A
            return assignments
            
    # If A is a hole, assign it to B
    if A.type == "Hole":
        if A.handle in assignments:
            return assignments if assignments[A.handle] == B else None
        else:
            assignments[A.handle] = B
            return assignments


    # Check type compatibility
    if A.type != B.type:
        return None

    # Check handle and children count match
    if A.handle != B.handle or len(A.children) != len(B.children):
        return None

    # Recursively match all children and merge assignments
    for A_child, B_child in zip(A.children, B.children):
        found = match(A_child, B_child)
        if found is None:
            return None
        # Simple merge: update with new assignments
        # (assuming no conflicts since terms have no common holes)
        assignments.update(found)

    return assignments


def apply(B: Object, assignments: Dict[str, Object]) -> Object:
    """
    Applies assignments to a term with holes, filling in the holes.
    """
    if B.type == "Hole":
        if B.handle in assignments:
            return assignments[B.handle]
        else:
            return B
    else:
        new_children = tuple(apply(child, assignments) for child in B.children)
        return Object(B.type, new_children, B.handle, B.repr_func, B.data)

def compose_rews(A: Object, B: Object) -> Optional[Object]:
    """
    Compose two rewritings, and get a rewriting.
    """
    if B.type != "Rew" or (A.symbol != B.symbol):
        return None

    # We first want to rename all holes in A and B to avoid conflicts with A's holes in the assignments.
    A_renamed = prefix_holes(A, "A_")
    B_renamed = prefix_holes(B, "B_")
    assignements = match(A_renamed.right, B_renamed.left)
    if assignements is not None:
        new_A = unprefix_holes(apply(A_renamed.left, assignements), ["A_", "B_"])
        new_B = unprefix_holes(apply(B_renamed.right, assignements), ["A_", "B_"])
        result = Rew(new_A, A.symbol, new_B)
        return result
    return None

def compose(A: Object, B: Object) -> Optional[Object]:
    """
    Apply a rewriting to an object, and get an object.
    You can also compose two rewritings (match A's right with B's left), and get a rewriting.
    """

    attempt = compose_rews(A, B)
    if attempt is not None:
        return attempt
    attempt_identified = compose_rews(identify(A, B.symbol), B)
    if attempt_identified is not None:
        return attempt_identified.right
    return None

def reduce_once(term: Object) -> Object:
    """
    Finds all the non-overlapping compositions in the term and applies the rule if possible.
    Returns the "1-step parallel" reduced term, or the original term if no reduction is possible.
    """
    if term.type == "Comp":
        attempt = compose(term.left, term.right)
        if attempt is not None:
            return attempt
    new_children = tuple(reduce_once(child) for child in term.children)
    return Object(term.type, new_children, term.handle, term.repr_func, term.data)

def reduce(term: Object, max_steps: int = 100) -> Object:
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
