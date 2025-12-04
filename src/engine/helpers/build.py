"""
Build Helper

Manages objects building.
"""

from typing import Tuple, List
from dataclasses import replace
from .helper import Helper, hookify
from ...core import Object, Term, check, reduce
from .utils.build import BuildState, build_start, build_use, build_clear


class BuildHelper(Helper[BuildState]):
    """
    Manages objects building.
    State: BuildState (working_term, working_term_unreduced)
    """

    def __init__(self) -> None:
        super().__init__(BuildState())
        self.register_handler('Start', self.handle_start)
        self.register_handler('Use', self.handle_use)
        self.register_handler('Clear', self.handle_clear)
        self.register_handler('Check', self.handle_check)
        self.register_handler('Reduce', self.handle_reduce)
        self.register_hook(['Done'], self.done_forhook)

    @hookify
    def handle_start(self, directive: str, initial_term: Object) -> Tuple[bool, List[Object]]:
        """Start forward-chaining from an initial term."""
        new_state, result = build_start(initial_term)
        self.set_state(new_state)
        return True, [result]

    @hookify
    def handle_use(self, directive: str, rule: Object) -> Tuple[bool, List[Object]]:
        """Apply a rewriting rule to the working term."""
        success, new_state, result = build_use(self.state, rule)
        if success:
            self.set_state(new_state)
        return success, [result]

    @hookify
    def handle_clear(self, directive: str) -> Tuple[bool, List[Object]]:
        """Clear the working term."""
        new_state, result = build_clear()
        self.set_state(new_state)
        return True, [result]

    @hookify
    def done_forhook(self, directive: str) -> List[Object]:
        """Inject working_term as argument to Done directive."""
        if self.state.working_term_unreduced is None:
            return []
        return [self.state.working_term_unreduced]

    @hookify
    def handle_check(self, directive: str, obj: Object = None) -> Tuple[bool, List[Object]]:
        """Check buildability of obj, or working_term if no argument."""
        target = obj if obj is not None else self.state.working_term
        if target is None:
            return False, [Term("Error", data={"result": "No term to check"})]
        success, message = check(target)
        return success, [replace(target, data={**target.data, "result": message})]

    @hookify
    def handle_reduce(self, directive: str, obj: Object) -> Tuple[bool, List[Object]]:
        reduced = reduce(obj)
        return True, [reduced]
