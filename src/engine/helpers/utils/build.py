from typing import Optional, Tuple
from dataclasses import dataclass
from ....core import Object, Comp, Term, reduce, identify, Rew
from ....core.operations import compose_rews


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

    # Reduce the rule first (allows using compositions of rules)
    rule_reduced = reduce(rule)

    if rule_reduced.type != "Rew":
        return False, state, Object(
            rule.type, rule.children, rule.handle, rule.repr_func,
            {**rule.data, "result": "Use requires a rewriting rule"}
        )

    # Get rewriting symbol from the rule
    rew_symbol = rule_reduced.symbol

    # Branch based on whether working_term is already a rewriting
    if state.working_term.type == "Rew":
        # Already building a rewriting - verify symbol matches
        if state.working_term.symbol != rew_symbol:
            return False, state, Object(
                rule_reduced.type, rule_reduced.children, rule_reduced.handle, rule_reduced.repr_func,
                {**rule_reduced.data, "result": f"Symbol mismatch: working term uses {state.working_term.symbol}, rule uses {rew_symbol}"}
            )
        # Compose two rewritings
        composed = compose_rews(state.working_term, rule_reduced)
        if composed is None:
            return False, state, Object(
                rule_reduced.type, rule_reduced.children, rule_reduced.handle, rule_reduced.repr_func,
                {**rule_reduced.data, "result": f"Cannot apply [] to {state.working_term}"}
            )
        composed = reduce(composed)
        # Unreduced: append to existing chain
        unreduced_chain = Comp(state.working_term_unreduced, rule)
    else:
        # First use - create identity rewriting
        identity = identify(state.working_term, rew_symbol)
        composed = compose_rews(identity, rule_reduced)
        if composed is None:
            return False, state, Object(
                rule_reduced.type, rule_reduced.children, rule_reduced.handle, rule_reduced.repr_func,
                {**rule_reduced.data, "result": f"Cannot apply [] to {state.working_term}"}
            )
        composed = reduce(composed)
        # Unreduced: create identity from unreduced form and compose
        identity_unreduced = identify(state.working_term_unreduced, rew_symbol)
        unreduced_chain = Comp(identity_unreduced, rule)

    # Build new state with rewriting (not just term)
    new_state = BuildState(
        working_term=composed,
        working_term_unreduced=unreduced_chain
    )
    to_display = composed.right
    result = Object(
        to_display.type, to_display.children, to_display.handle, to_display.repr_func,
        {**to_display.data, "result": "Applied rule, new term: []"}
    )
    return True, new_state, result


def build_clear() -> Tuple[BuildState, Object]:
    """Clear the working term. Returns (new_state, result)."""
    return BuildState(), Term("Cleared", data={"result": "Working term cleared"})