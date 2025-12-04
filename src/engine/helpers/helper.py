"""
Helper Base Class

Helpers are the core components of the proof assistant pipeline.
Each helper has:
- State: Single immutable value (managed via stack for undo/breakpoint/rollback)
- Hooks: Pre-processing for specific directives (run BEFORE handling)
- Handlers: Final processing for specific directives

The pipeline routes each directive through registered hooks, then to the registered handler.
"""

from abc import ABC
from typing import Dict, List, Tuple, Any, Optional, Callable, TypeVar, Generic
from functools import wraps
import inspect
from ...core import Object

T = TypeVar('T')
S = TypeVar('S')  # State type


def hookify(f: Callable[..., T]) -> Callable[[str, List[Object]], T]:
    """Decorator to adapt methods with explicit parameters to the directive interface.

    Use on both hooks and handlers:
        @hookify
        def my_hook(self, directive: str, arg1, arg2, ...) -> List[Object]:
            ...

        @hookify
        def my_handler(self, directive: str, arg1, arg2=default, ...) -> Tuple[bool, List[Object]]:
            ...

    The decorated method will accept: (directive: str, arguments: List[Object])
    """
    sig = inspect.signature(f)
    params = list(sig.parameters.values())

    # Count required params (excluding 'self' and 'directive')
    required = sum(1 for p in params[2:]
                   if p.default is inspect.Parameter.empty
                   and p.kind != inspect.Parameter.VAR_POSITIONAL
                   and p.kind != inspect.Parameter.VAR_KEYWORD)
    optional = sum(1 for p in params[2:]
                   if p.default is not inspect.Parameter.empty)
    has_var_positional = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params[2:])

    @wraps(f)
    def wrapper(*args, **kwargs):
        if len(args) != 3:
            raise TypeError(f"Unexpected number of arguments to {f.__name__}: {len(args)}")
        self_arg, directive, arguments = args

        # Validate argument count
        if not has_var_positional:
            arg_count = len(arguments)
            if arg_count < required:
                raise TypeError(f"{f.__name__} requires at least {required} arguments, got {arg_count}")
            if arg_count > required + optional:
                raise TypeError(f"{f.__name__} accepts at most {required + optional} arguments, got {arg_count}")

        return f(self_arg, directive, *arguments, **kwargs)

    return wrapper


class Helper(ABC, Generic[S]):
    """
    Base class for all helpers in the proof assistant pipeline.

    Each helper can:
    1. Register forhooks to pre-process specific directives
    2. Register handlers to fully process specific directives
    3. Register backhooks to post-process results
    4. Maintain immutable state with undo/breakpoint/rollback support

    State Management:
    - self.state: Current immutable state (any immutable value: None, tuple, frozen dataclass, etc.)
    - self.set_state(new): Replace state, pushing to history stack
    - self.undo(): Pop last state from stack
    - self.breakpoint(name): Mark current position for rollback
    - self.rollback(name): Return to named breakpoint

    Workflow:
    - Forhooks: (str, List[Object]) -> List[Object] - receive directive and arguments, return modified arguments
    - Handlers: (str, List[Object]) -> Tuple[bool, List[Object]] - return success flag and result objects
    - Backhooks: (str, List[Object]) -> List[Object] - receive directive and results, return modified results
    - 'ALL' is a special directive type that matches all directives
    """

    def __init__(self, initial_state: S = None):
        """Initialize the helper with optional initial state"""
        self.forhooks = {}  # directive_type -> forhook_method
        self.handlers = {}  # directive -> handler_method
        self.backhooks = {}  # directive_type -> backhook_method
        self.hooks_state = {}  # per-traversal state, cleared each run

        # State management
        self._state: S = initial_state
        self._state_stack: List[S] = [initial_state]
        self._breakpoints: Dict[str, int] = {}  # name -> stack index

    @property
    def state(self) -> S:
        """Read-only access to current state"""
        return self._state

    def set_state(self, new_state: S) -> None:
        """Replace state, pushing to history stack"""
        self._state = new_state
        self._state_stack.append(new_state)

    def undo(self) -> bool:
        """Pop last state. Returns False if at initial state."""
        if len(self._state_stack) <= 1:
            return False
        self._state_stack.pop()
        self._state = self._state_stack[-1]
        return True

    def breakpoint(self, name: str) -> None:
        """Mark current stack position with name"""
        self._breakpoints[name] = len(self._state_stack) - 1

    def rollback(self, name: str) -> bool:
        """Return to named breakpoint. Returns False if not found."""
        if name not in self._breakpoints:
            return False
        idx = self._breakpoints[name]
        self._state_stack = self._state_stack[:idx + 1]
        self._state = self._state_stack[-1]
        # Remove breakpoints beyond this point
        self._breakpoints = {k: v for k, v in self._breakpoints.items() if v <= idx}
        return True

    def stack_depth(self) -> int:
        """Return current stack depth (for Pipeline coordination)"""
        return len(self._state_stack)

    def truncate_to(self, depth: int) -> None:
        """Truncate stack to given depth (for Pipeline coordination)"""
        if depth < len(self._state_stack):
            self._state_stack = self._state_stack[:depth]
            self._state = self._state_stack[-1]
            self._breakpoints = {k: v for k, v in self._breakpoints.items() if v < depth}


    def register_hook(self, directives: List[str],
                         forhook_method: Callable[[str, List[Object]], List[Object]],
                         backhook_method: Optional[Callable[[str, List[Object]], List[Object]]] = None):
        """
        Register a forhook (and optional backhook) for specific directive types.
        Forhook signature: (directive: str, arguments: List[Object]) -> List[Object]
        Backhook signature: (directive: str, results: List[Object]) -> List[Object]

        Decorate your hook methods with @hookify to adapt explicit parameters.
        """
        for directive in directives:
            self.forhooks[directive] = forhook_method
            if backhook_method is not None:
                self.backhooks[directive] = backhook_method

    def register_handler(self, directive: str, handler_method: Callable[[str, List[Object]], Tuple[bool, List[Object]]]):
        """
        Register a handler for a specific directive type.
        Handler signature: (directive: str, arguments: List[Object]) -> Tuple[bool, List[Object]]

        Decorate your handler methods with @hookify to adapt explicit parameters.
        """
        self.handlers[directive] = handler_method

    def get_hook(self, directive: str):
        """Get forhook and optional backhook for the given directive type.

        Returns: Tuple[Optional[Callable], Optional[Callable]]
                 (forhook_method, backhook_method or None)
        Supports 'ALL' wildcard.
        """
        forhook = None
        backhook = None

        if directive in self.forhooks:
            forhook = self.forhooks[directive]
            backhook = self.backhooks.get(directive)
        elif 'ALL' in self.forhooks:
            forhook = self.forhooks['ALL']
            backhook = self.backhooks.get('ALL')

        return (forhook, backhook)

    def get_handler(self, directive: str) -> bool:
        """Check if this helper has a handler for the given directive type"""
        if directive in self.handlers:
            return self.handlers[directive]

    def reset_hooks_state(self):
        """Called at start of each pipeline traversal to clear per-traversal state"""
        self.hooks_state.clear()