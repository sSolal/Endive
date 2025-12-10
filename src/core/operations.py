"""
Core Engine for Endive Proof Assistant

This module defines the fundamental data manipulation operations:
- Pattern matching
- Substitution
- Application reduction
"""

from typing import Optional, Dict, List
from .objects import Object,Term, Hole, Rew, Comp, identify
from .utils import get_hole_names

def rename_holes(term: Object, rename_map: Dict[str, str]) -> Object:
    if term.type == "Hole":
        new_handle = rename_map.get(term.handle, term.handle)
        if new_handle != term.handle:
            return Hole(new_handle, dict(term.data))
        return term

    new_children = tuple(rename_holes(child, rename_map) for child in term.children)
    if new_children != term.children:
        return Object(term.type, new_children, term.handle, term.repr_func, dict(term.data))
    return term

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


def match(A: Object, B: Object, assignments: Optional[Dict[str, Object]] = None) -> Optional[Dict[str, Object]]:
    """
    Bidirectional syntactic unification of A and B.
    Returns a dictionary of assignments for holes in both A and B such that
    when applied to both terms, they become identical. Returns None if unification fails.
    """
    if assignments is None:
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

    # Recursively match all children, threading assignments through
    for A_child, B_child in zip(A.children, B.children):
        assignments = match(A_child, B_child, assignments)
        if assignments is None:
            return None

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
        return Object(B.type, new_children, B.handle, B.repr_func, dict(B.data))

def compose_rews(A: Object, B: Object) -> Optional[Object]:
    """
    Compose two rewritings, and get a rewriting.
    """
    if A.type != "Rew" or B.type != "Rew" or (A.symbol != B.symbol):
        return None

    # Collect all hole names from both rules
    holes_A = get_hole_names(A)
    holes_B = get_hole_names(B)

    rename_map = {}
    reserved_names = holes_A.copy()

    for hole_name in holes_B:
        if hole_name in reserved_names:
            # Add primes until unique
            new_name = hole_name + "'"
            while new_name in reserved_names:
                new_name += "'"
            rename_map[hole_name] = new_name
            reserved_names.add(new_name)

    B_renamed = rename_holes(B, rename_map) if rename_map else B

    # Match and compose
    assignments = match(A.right, B_renamed.left)
    if assignments is not None:
        new_A = apply(A.left, assignments)
        new_B = apply(B_renamed.right, assignments)
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

    # First, reduce all children
    new_children = tuple(reduce_once(child) for child in term.children)
    result = Object(term.type, new_children, term.handle, term.repr_func, dict(term.data))

    if result != term:
        term = result

    # Then, if this is a composition, try to compose
    if term.type == "Comp":
        attempt = compose(term.left, term.right)
        if attempt is not None:
            return attempt
    return term

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
