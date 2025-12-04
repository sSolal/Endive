from typing import Optional, Tuple
from dataclasses import dataclass
from ....core import Object, Comp, Term, reduce


@dataclass(frozen=True)
class BuildState:
    """Immutable state for forward-chaining term construction"""
    working_term: Optional[Object] = None  # Reduced form for display
    working_term_unreduced: Optional[Object] = None  # Unreduced form for buildability checking


def build_start(initial_term: Object) -> Tuple[BuildState, Object]:
    """Start forward-chaining from an initial term. Returns (new_state, result)."""
    reduced = reduce(initial_term)
    new_state = BuildState(working_term=reduced, working_term_unreduced=initial_term)
    result = Object(
        reduced.type, reduced.children, reduced.handle, reduced.repr_func,
        {**reduced.data, "result": "Started building from: []"}
    )
    return new_state, result


def build_use(state: BuildState, rule: Object) -> Tuple[bool, BuildState, Object]:
    """Apply a rewriting rule. Returns (success, new_state, result)."""
    if state.working_term_unreduced is None:
        return False, state, Object(
            rule.type, rule.children, rule.handle, rule.repr_func,
            {**rule.data, "result": "No working term. Use 'Start' first."}
        )

    if rule.type != "Rew":
        return False, state, Object(
            rule.type, rule.children, rule.handle, rule.repr_func,
            {**rule.data, "result": "Use requires a rewriting rule"}
        )

    composition = Comp(state.working_term, rule)
    reduced = reduce(composition)

    if reduced == composition:
        return False, state, Object(
            rule.type, rule.children, rule.handle, rule.repr_func,
            {**rule.data, "result": f"Cannot apply [] to {state.working_term}"}
        )

    new_state = BuildState(
        working_term=reduced,
        working_term_unreduced=Comp(state.working_term_unreduced, rule)
    )
    result = Object(
        reduced.type, reduced.children, reduced.handle, reduced.repr_func,
        {**reduced.data, "result": "Applied rule, new term: []"}
    )
    return True, new_state, result


def build_clear() -> Tuple[BuildState, Object]:
    """Clear the working term. Returns (new_state, result)."""
    return BuildState(), Term("Cleared", data={"result": "Working term cleared"})