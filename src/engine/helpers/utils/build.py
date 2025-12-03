from typing import Optional, Tuple
from dataclasses import dataclass
from ....core import Object, Comp, Term, reduce

@dataclass
class BuildState:
    """Manages forward-chaining term construction"""
    working_term: Optional[Object] = None  # Reduced form for display
    working_term_unreduced: Optional[Object] = None  # Unreduced form for buildability checking

    def start(self, initial_term: Object) -> Object:
        """Start forward-chaining from an initial term."""
        self.working_term = reduce(initial_term)
        self.working_term_unreduced = initial_term
        return Object(
            self.working_term.type,
            self.working_term.children,
            self.working_term.handle,
            self.working_term.repr_func,
            {**self.working_term.data, "result": "Started building from: []"}
        )

    def use(self, rule: Object) -> Tuple[bool, Object]:
        """Apply a rewriting rule to the working term."""
        if self.working_term_unreduced is None:
            return False, Object(
                rule.type, rule.children, rule.handle, rule.repr_func,
                {**rule.data, "result": "No working term. Use 'Start' first."}
            )

        if rule.type != "Rew":
            return False, Object(
                rule.type, rule.children, rule.handle, rule.repr_func,
                {**rule.data, "result": "Use requires a rewriting rule"}
            )

        composition = Comp(self.working_term, rule)
        reduced = reduce(composition)

        if reduced == composition:
            return False, Object(
                rule.type, rule.children, rule.handle, rule.repr_func,
                {**rule.data, "result": f"Cannot apply [] to {self.working_term}"}
            )

        self.working_term = reduced
        self.working_term_unreduced = Comp(self.working_term_unreduced, rule)
        return True, Object(
            reduced.type, reduced.children, reduced.handle, reduced.repr_func,
            {**reduced.data, "result": "Applied rule, new term: []"}
        )

    def clear(self) -> Object:
        """Clear the working term."""
        self.working_term = None
        self.working_term_unreduced = None
        return Term("Cleared", data={"result": "Working term cleared"})