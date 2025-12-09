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

from typing import List, Tuple, Dict, Optional
from .helpers import Helper
from ..core import Object, Term


class Pipeline:
    """
    Orchestrates the processing of directives through helpers.

    The pipeline maintains:
    - List of helpers (order matters for hooks)
    - Stack of (directive, helper) pairs for each processed directive (for undo)
    """

    def __init__(self):
        self.helpers: List[Helper] = []
        self.handler_stack: List[Tuple[str, Helper]] = []  # Track (directive, helper) for each directive
        self.breakpoints: Dict[str, int] = {}  # name -> handler_stack depth at checkpoint

    def undo(self) -> Tuple[bool, Optional[str]]:
        """Undo the last directive. Returns (False, None) if nothing to undo, otherwise (True, directive_name)."""
        if not self.handler_stack:
            return False, None
        directive, helper = self.handler_stack.pop()
        helper.undo()  # Always undo state, even if it returns False
        return True, directive

    def breakpoint(self, name: str) -> None:
        """Create named breakpoint across all helpers and pipeline."""
        self.breakpoints[name] = len(self.handler_stack)
        for helper in self.helpers:
            helper.breakpoint(name)

    def rollback(self, name: str) -> bool:
        """Rollback all helpers to named breakpoint. Returns False if not found."""
        if name not in self.breakpoints:
            return False
        if not all(name in h.breakpoints for h in self.helpers):
            return False

        # Rollback handler stack to checkpoint depth
        stack_depth = self.breakpoints[name]
        self.handler_stack = self.handler_stack[:stack_depth]

        # Rollback all helpers
        for helper in self.helpers:
            helper.rollback(name)

        # Remove checkpoints beyond this point
        self.breakpoints = {k: v for k, v in self.breakpoints.items() if v <= stack_depth}

        return True

    def process(self, directive: str, arguments: List[Object]) -> Tuple[bool, List[Object]]:
        """
        Process a directive through the pipeline.
        """

        # Phase 1: Apply forhooks in forward order, collect backhooks
        backhooks_to_run = []  # Store backhooks to run in reverse
        for helper in self.helpers:
            hooks = helper.get_hooks(directive)
            if hooks:
                helper.reset_hooks_state()
                # Apply all matching forhooks for this helper in registration order
                for forhook, backhook in hooks:
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
            self.handler_stack.append((directive, handling_helper))

        # Phase 3: Apply backhooks in reverse order
        for backhook in reversed(backhooks_to_run):
            results = backhook(directive, results)

        return success, results