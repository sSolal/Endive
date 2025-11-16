"""
Helper Base Class

Helpers are the core components of the proof assistant pipeline.
Each helper has:
- State: Internal data (goals, aliases, rules, etc.)
- Hooks: Pre-processing for specific directives (run BEFORE handling)
- Handlers: Final processing for specific directives

The pipeline routes each directive through registered hooks, then to the registered handler.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional


class Helper(ABC):
    """
    Base class for all helpers in the proof assistant pipeline.

    Each helper can:
    1. Register hooks to pre-process specific directives
    2. Register handlers to fully process specific directives
    3. Maintain internal state

    Workflow:
    - Hooks run BEFORE handlers and can modify content/context
    - Handlers fully process a directive and return success/message/result
    - 'ALL' is a special directive type that matches all directives
    """

    def __init__(self):
        """Initialize the helper with empty state"""
        self.hooks = {}  # directive_type -> hook_method
        self.handlers = {}  # directive -> handler_method

   
    def register_hook(self, directives, hook_method):
        """
        Register a hook for a specific directive type.
        """
        for directive in directives:
                self.hooks[directive] = hook_method

    def register_handler(self, directive: str, handler_method):
        """
        Register a handler for a specific directive type.
        """
        self.handlers[directive] = handler_method

    def get_hook(self, directive: str) -> bool:
        """Check if this helper has a hook for the given directive type"""
        if directive in self.hooks:
            return self.hooks[directive]
        elif 'ALL' in self.hooks:
            return self.hooks['ALL']
        return None

    def get_handler(self, directive: str) -> bool:
        """Check if this helper has a handler for the given directive type"""
        if directive in self.handlers:
            return self.handlers[directive]

    def clear(self):
        pass