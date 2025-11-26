"""
Pipeline Module

The Pipeline orchestrates the flow of directives through helpers.

Flow:
1. Parser produces (directive_type, content)
2. Pipeline applies all registered hooks in order
3. Pipeline calls the registered handler
4. Pipeline returns result
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

        Workflow:
        1. Apply all hooks in order (each helper that registered a hook for this directive)
        2. Find the handler for this directive
        3. Call the handler
        4. Return (success: bool, results: List[Object])
        """

        # Phase 1: Apply all hooks in order
        for helper in self.helpers:
            hook = helper.get_hook(directive)
            if hook is not None:
                arguments = hook(directive, arguments)

        # Phase 2: Find and call handler
        handler_helper = None
        for helper in self.helpers:
            handler = helper.get_handler(directive)
            if handler is not None:
                return handler(directive, arguments)

        return False, [Term("Error", data={"result": f"No handler registered for directive: {directive}"})]

    def clear(self):
        for helper in self.helpers:
            helper.clear()