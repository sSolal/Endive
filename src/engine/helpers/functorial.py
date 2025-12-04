"""
Functorial Helper

Manages functorial rewriting rules that automatically wrap rules based on position.

Usage:
  Functorial inner_rew, term_symbol, position, outer_rew, rule
  Use rule, pos1, pos2, pos3  # Positions are child indices
"""

from typing import List, Tuple
from dataclasses import replace
from .helper import Helper, hookify
from ...core import Object, Term, Comp, reduce, extract_integer
from .utils.functorial import FunctorialState, get_functorial, add_functorial


class FunctorialHelper(Helper[FunctorialState]):
    """
    Manages functorial rewriting rules for automatic rule wrapping.

    State: tuple of ((key), (value)) pairs
    """

    def __init__(self, build_helper) -> None:
        super().__init__(())  # Empty tuple as initial state
        self.build_helper = build_helper  # Cross-helper reference (not part of state)
        self.register_handler('Functorial', self.handle_functorial)
        self.register_hook(['Use'], self.use_forhook)

    @hookify
    def handle_functorial(self, directive: str, inner_rew: Object, term_symbol: Object,
                          position: Object, outer_rew: Object, rule: Object) -> Tuple[bool, List[Object]]:
        """
        - inner_rew: Symbol of the rewriting that this functorial wraps (e.g., "=")
        - term_symbol: Term constructor this applies to (e.g., "f")
        - position: Child index where the rewriting occurs (e.g., 0, 1, 2)
        - outer_rew: Symbol of the resulting rewriting (e.g., "=")
        - rule: The functorial rule itself

        Example: Functorial =, f, 0, =, ([a] = [b]) => (f([a], [x], [y]) = f([b], [x], [y]))
        """
        if inner_rew.type != 'Term' or len(inner_rew.children) != 0:
            return False, [replace(inner_rew, data={**inner_rew.data,
                "result": "inner_rew must be a simple term (symbol)"})]

        if term_symbol.type != 'Term' or len(term_symbol.children) != 0:
            return False, [replace(term_symbol, data={**term_symbol.data,
                "result": "term_symbol must be a simple term (symbol)"})]

        if outer_rew.type != 'Term' or len(outer_rew.children) != 0:
            return False, [replace(outer_rew, data={**outer_rew.data,
                "result": "outer_rew must be a simple term (symbol)"})]

        pos_int = extract_integer(position)
        if pos_int is None:
            return False, [replace(position, data={**position.data,
                "result": "position must be a number"})]

        if rule.type != 'Rew':
            return False, [replace(rule, data={**rule.data,
                "result": "Functorial rule must be a rewriting"})]

        self.set_state(add_functorial(
            self.state, inner_rew.handle, term_symbol.handle, pos_int, outer_rew.handle, rule
        ))

        return True, [replace(rule, data={**rule.data,
            "result": f"Functorial registered for {term_symbol.handle} at position {pos_int}"})]

    @hookify
    def use_forhook(self, directive: str, rule: Object, *positions: Object) -> List[Object]:
        """
        Hook for Use directive: wrap rule with functorial rules if positions provided.

        Arguments:
        - rule: The rewriting rule to apply
        - *positions: Optional sequence of child indices specifying where to apply
        """
        if not positions:
            return [rule]

        # Extract position integers
        pos_indices = []
        for pos_obj in positions:
            pos_int = extract_integer(pos_obj)
            if pos_int is None:
                # Return error wrapped in the rule
                return [replace(rule, data={**rule.data,
                    "result": f"Position must be a number, got: {pos_obj}"})]
            pos_indices.append(pos_int)

        # Wrap the rule
        try:
            wrapped_rule = self.wrap_rule(rule, pos_indices)
            return [wrapped_rule]
        except ValueError as e:
            # Return error wrapped in the rule
            return [replace(rule, data={**rule.data, "result": str(e)})]

    def wrap_rule(self, rule: Object, positions: List[int]) -> Object:
        """
        Wrap a rule with functorial rules based on positions.

        Algorithm:
        1. Navigate to target position in working_term
        2. Build path of (term_symbol, position_idx) pairs
        3. Wrap rule with functorials from innermost to outermost (reversed path)

        Raises ValueError if working_term is None or functorial not found.
        """
        # Get working term from BuildHelper
        working_term = self.build_helper.state.working_term
        if working_term is None:
            raise ValueError("No working term. Use 'Start' before 'Use' with positions.")

        # Verify rule is a rewriting
        if rule.type != 'Rew':
            raise ValueError("Can only wrap rewriting rules")

        # Navigate to build the path
        path = []
        current_term = working_term

        for pos_idx in positions:
            # Check bounds
            if pos_idx < 0 or pos_idx >= len(current_term.children):
                raise ValueError(f"Position {pos_idx} out of bounds for term {current_term.handle}")

            # Record this step
            path.append((current_term.handle, pos_idx))

            # Navigate down
            current_term = current_term.children[pos_idx]

        # Wrap from innermost to outermost (reverse path)
        wrapped_rule = rule
        current_inner_rew = rule.symbol

        for term_symbol, position_idx in reversed(path):

            # Lookup functorial rule
            functorial_data = get_functorial(
                self.state, current_inner_rew, term_symbol, position_idx
            )

            if functorial_data is None:
                raise ValueError(
                    f"No functorial rule for ({current_inner_rew}, {term_symbol}, {position_idx})"
                )

            outer_rew, functorial = functorial_data

            # Compose wrapped_rule with functorial using Comp and reduce
            composition = Comp(wrapped_rule, functorial)
            wrapped_rule = reduce(composition)

            # Update inner_rew for next iteration
            current_inner_rew = outer_rew

        return wrapped_rule
