"""
Pipeline Module

The Pipeline orchestrates the flow of directives through helpers.

Flow:
1. Parser produces (directive_type, content)
2. Pipeline applies all registered forhooks in forward order
3. Pipeline calls the registered handler
4. Pipeline applies all registered backhooks in reverse order
5. Pipeline returns result

State Management:
- undo(): Revert last handler's state change
- breakpoint(name): Create named rollback point
- rollback(name): Return all helpers to named breakpoint
"""

from typing import List, Tuple, Dict
from .helpers import Helper
from ..core import Object, Term


class Pipeline:
    """
    Orchestrates the processing of directives through helpers.

    The pipeline maintains:
    - List of helpers (order matters for hooks)
    - Stack of which helper handled each directive (for undo)
    """

    def __init__(self):
        self.helpers: List[Helper] = []
        self._handler_stack: List[Helper] = []  # Track which helper handled each directive

    def undo(self) -> bool:
        """Undo the last handler's state change. Returns False if nothing to undo."""
        if not self._handler_stack:
            return False
        helper = self._handler_stack.pop()
        return helper.undo()

    def breakpoint(self, name: str) -> None:
        """Create named breakpoint across all helpers."""
        for helper in self.helpers:
            helper.breakpoint(name)

    def rollback(self, name: str) -> bool:
        """Rollback all helpers to named breakpoint. Returns False if not found."""
        if not all(name in h._breakpoints for h in self.helpers):
            return False
        for helper in self.helpers:
            helper.rollback(name)
        return True

    def process(self, directive: str, arguments: List[Object]) -> Tuple[bool, List[Object]]:
        """
        Process a directive through the pipeline.
        """

        # Phase 1: Apply forhooks in forward order, collect backhooks
        backhooks_to_run = []  # Store backhooks to run in reverse
        for helper in self.helpers:
            forhook, backhook = helper.get_hook(directive)
            if forhook is not None:
                helper.reset_hooks_state()
                arguments = forhook(directive, arguments)
                # Store backhook if present (will run in reverse order)
                if backhook is not None:
                    backhooks_to_run.append(backhook)

        # Phase 2: Find and call handler
        result = None
        handling_helper = None
        for helper in self.helpers:
            handler = helper.get_handler(directive)
            if handler is not None:
                handling_helper = helper
                result = handler(directive, arguments)
                break

        if result is None:
            return False, [Term("Error", data={"result": f"No handler registered for directive: {directive}"})]

        success, results = result

        # Track which helper handled this directive (for undo)
        if handling_helper is not None:
            self._handler_stack.append(handling_helper)

        # Phase 3: Apply backhooks in reverse order
        for backhook in reversed(backhooks_to_run):
            results = backhook(directive, results)

        return success, results