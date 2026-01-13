from typing import Optional, Tuple
from dataclasses import dataclass
from ....core import Object, Comp, Term, reduce, identify, Rew
from ....core.operations import compose_rews, compose


@dataclass(frozen=True)
class BuildState:
    """Immutable state for forward-chaining term construction"""
    working_term: Optional[Object] = None  # Reduced form for display
    working_term_unreduced: Optional[Object] = None  # Unreduced form for buildability checking
    term_stack: Tuple[Object, ...] = ()  # Stack of finalized terms (unreduced forms, to preserve nested structure)


def finalize_term(state: BuildState) -> BuildState:
    """
    Finalize current working term by adding to stack.
    Stores unreduced form to preserve nested Comp structure.
    Returns new BuildState. If no working term or already in stack, returns unchanged.
    """
    if state.working_term_unreduced is None:
        return state

    # Check if already in stack (avoid duplicates)
    if state.working_term_unreduced in state.term_stack:
        return state

    # Add unreduced form to stack
    new_stack = state.term_stack + (state.working_term_unreduced,)

    return BuildState(
        working_term=state.working_term,
        working_term_unreduced=state.working_term_unreduced,
        term_stack=new_stack
    )


def build_start(state: BuildState, initial_term: Object) -> Tuple[BuildState, Object]:
    """
    Start forward-chaining from an initial term.
    Finalizes current working term before starting new one.
    Returns (new_state, result).
    """
    # Finalize current working term
    finalized_state = finalize_term(state)

    # Start new term
    reduced = reduce(initial_term)
    new_state = BuildState(
        working_term=reduced,
        working_term_unreduced=initial_term,
        term_stack=finalized_state.term_stack  # Preserve stack
    )
    result = Object(
        reduced.type, reduced.children, reduced.handle, reduced.repr_func,
        {**reduced.data, "result": "Started building from: []"}
    )
    return new_state, result


def try_stack_application(term_stack: Tuple[Object, ...], rule: Object) -> Optional[Tuple[Object, Object]]:
    """
    Phase 2: Try to apply rule to stack backwards.

    Stack stores unreduced forms for structure preservation,
    but composition uses reduced forms to check if it works.
    Results preserve both unreduced and reduced forms.

    Returns None if no match, or (unreduced_form, reduced_form) if success.
    unreduced_form preserves nested Comps: (A | (B | rule))
    """
    if not term_stack:
        return None

    result_reduced = reduce(rule)
    result_unreduced = rule
    matched_count = 0

    # Iterate backwards (most recent first)
    for term_unreduced in reversed(term_stack):
        # Reduce the stack term for composition check
        term_reduced = reduce(term_unreduced)

        # Try composition using compose() function (handles identification if needed)
        # This properly tests if composition succeeds (returns None on failure)
        composed = compose(term_reduced, result_reduced)

        if composed is None:
            break  # Stop at first failure

        # Success - build unreduced form with original unreduced stack term
        result_reduced = composed
        result_unreduced = Comp(term_unreduced, result_unreduced)
        matched_count += 1

    # Success if matched at least one
    return (result_unreduced, result_reduced) if matched_count > 0 else None


def build_use(state: BuildState, rule: Object) -> Tuple[bool, BuildState, Object]:
    """
    Apply a rewriting rule using two-phase logic.
    Phase 1: Right-composition with working term (existing behavior)
    Phase 2: Apply rule to stack backwards (fallback if Phase 1 fails)
    Returns (success, new_state, result).
    """
    # Reduce the rule first (allows using compositions of rules)
    rule_reduced = reduce(rule)

    if rule_reduced.type != "Rew":
        return False, state, Object(
            rule.type, rule.children, rule.handle, rule.repr_func,
            {**rule.data, "result": "Use requires a rewriting rule"}
        )

    # Get rewriting symbol from the rule
    rew_symbol = rule_reduced.symbol

    # === PHASE 1: Right-composition with working term ===
    phase1_error_obj = None

    if state.working_term_unreduced is None:
        phase1_error_obj = Object(
            rule.type, rule.children, rule.handle, rule.repr_func,
            {**rule.data, "result": "No working term. Use 'Start' first."}
        )
    else:
        # Branch based on whether working_term is already a rewriting
        if state.working_term.type == "Rew":
            # Already building a rewriting - verify symbol matches
            if state.working_term.symbol != rew_symbol:
                phase1_error_obj = Object(
                    rule_reduced.type, rule_reduced.children, rule_reduced.handle, rule_reduced.repr_func,
                    {**rule_reduced.data, "result": f"Symbol mismatch: working term uses {state.working_term.symbol}, rule uses {rew_symbol}"}
                )
            else:
                # Compose two rewritings
                composed = compose_rews(state.working_term, rule_reduced)
                if composed is None:
                    phase1_error_obj = Object(
                        rule_reduced.type, rule_reduced.children, rule_reduced.handle, rule_reduced.repr_func,
                        {**rule_reduced.data, "result": f"Cannot apply [] to {state.working_term}"}
                    )
                else:
                    composed = reduce(composed)
                    # Unreduced: append to existing chain
                    unreduced_chain = Comp(state.working_term_unreduced, rule)

                    # Phase 1 success
                    new_state = BuildState(
                        working_term=composed,
                        working_term_unreduced=unreduced_chain,
                        term_stack=state.term_stack
                    )
                    to_display = composed.right
                    result = Object(
                        to_display.type, to_display.children, to_display.handle, to_display.repr_func,
                        {**to_display.data, "result": "Applied rule, new term: []"}
                    )
                    return True, new_state, result
        else:
            # First use - create identity rewriting
            identity = identify(state.working_term, rew_symbol)
            composed = compose_rews(identity, rule_reduced)
            if composed is None:
                phase1_error_obj = Object(
                    rule_reduced.type, rule_reduced.children, rule_reduced.handle, rule_reduced.repr_func,
                    {**rule_reduced.data, "result": f"Cannot apply [] to {state.working_term}"}
                )
            else:
                composed = reduce(composed)
                # Unreduced: create identity from unreduced form and compose
                identity_unreduced = identify(state.working_term_unreduced, rew_symbol)
                unreduced_chain = Comp(identity_unreduced, rule)

                # Phase 1 success
                new_state = BuildState(
                    working_term=composed,
                    working_term_unreduced=unreduced_chain,
                    term_stack=state.term_stack
                )
                to_display = composed.right
                result = Object(
                    to_display.type, to_display.children, to_display.handle, to_display.repr_func,
                    {**to_display.data, "result": "Applied rule, new term: []"}
                )
                return True, new_state, result

    # === PHASE 2: Stack application (including current working term) ===
    # Build full stack: current working term + finalized terms
    if state.working_term_unreduced is not None:
        full_stack = state.term_stack + (state.working_term_unreduced,)
    else:
        full_stack = state.term_stack

    stack_result = try_stack_application(full_stack, rule)

    if stack_result is not None:
        unreduced_form, reduced_form = stack_result

        new_state = BuildState(
            working_term=reduced_form,
            working_term_unreduced=unreduced_form,
            term_stack=state.term_stack
        )

        # Display the whole term (like Start does), not just the right side
        result = Object(
            reduced_form.type, reduced_form.children, reduced_form.handle, reduced_form.repr_func,
            {**reduced_form.data, "result": "Applied rule to stack, new term: []"}
        )
        return True, new_state, result

    # Both phases failed - return Phase 1 error object (allows hooks to process it)
    return False, state, phase1_error_obj


def build_clear(state: BuildState) -> Tuple[BuildState, Object]:
    """
    Clear the working term after finalizing it.
    Preserves stack. Returns (new_state, result).
    """
    # Finalize current working term
    finalized_state = finalize_term(state)

    # Clear but preserve stack
    new_state = BuildState(
        working_term=None,
        working_term_unreduced=None,
        term_stack=finalized_state.term_stack
    )
    return new_state, Term("Cleared", data={"result": "Working term cleared"})