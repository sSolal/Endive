"""
Pipeline Module

The Pipeline orchestrates the flow of directives through helpers.

Flow:
1. Parser produces (directive_type, content)
2. Pipeline applies all registered forhooks in forward order
3. Pipeline calls the registered handler
4. Pipeline applies all registered backhooks in reverse order
5. Pipeline returns result
"""

from typing import List, Tuple, Any, Optional, Type
from .helpers import Helper
from ..core import Object, Term


class Pipeline:
    """
    Orchestrates the processing of directives through helpers.

    The pipeline maintains:
    - List of helpers (order matters for hooks)
    - Mapping of directive types to handlers
    """

    def __init__(self):
        self.helpers: List[Helper] = []

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
        for helper in self.helpers:
            handler = helper.get_handler(directive)
            if handler is not None:
                result = handler(directive, arguments)
                break

        if result is None:
            return False, [Term("Error", data={"result": f"No handler registered for directive: {directive}"})]

        success, results = result

        # Phase 3: Apply backhooks in reverse order
        for backhook in reversed(backhooks_to_run):
            results = backhook(directive, results)

        return success, results

    def clear(self):
        for helper in self.helpers:
            helper.clear()