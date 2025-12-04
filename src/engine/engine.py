"""
Proof Assistant (New Pipeline Architecture)

This engine takes a line of text, parses it, processes it through the pipeline, and returns the diagnoses in displayed format
"""

from typing import Tuple, List
from .pipeline import Pipeline
from .importer import ImportHandler
from ..core import Object, Term
from .helpers import (
    PeanoHelper,
    AliasHelper,
    GoalHelper,
    BuildHelper,
    FunctorialHelper
)
from .parser import parse_line, ParseError


class Engine:
    """

    The proof assistant maintains a pipeline of helpers that process directives.
    Each helper can hook into directives for pre-processing and/or handle them fully.

    The flow is:
    Directive + Term -> Pipeline (Hooks -> Handler) -> Terms + Diagnoses
    """

    def __init__(self) -> None:
        self.pipeline = Pipeline()
        self.importer = ImportHandler(self)

        # Register helpers in order
        # Order matters for hooks! They are applied in registration order.


        # Alias helper (should run after Peano to substitute names)
        self.alias_helper = AliasHelper()
        self.pipeline.helpers.append(self.alias_helper)

         # Build helper, should handle building objects
        self.build_helper = BuildHelper()
        self.pipeline.helpers.append(self.build_helper)

        # Functorial helper (requires BuildHelper reference)
        self.functorial_helper = FunctorialHelper(self.build_helper)
        self.pipeline.helpers.append(self.functorial_helper)

        # Peano helper (should run first to convert integers to/from Peano) (comes after helpers that may need numeric inputs)
        self.peano_helper = PeanoHelper()
        self.pipeline.helpers.append(self.peano_helper)

        # Goal helper, should handle most directives
        self.goal_helper = GoalHelper()
        self.pipeline.helpers.append(self.goal_helper)

       

    def process(self, line: str) -> Tuple[bool, List[Object]]:
        """
        Check a single line of proof using the pipeline.
        Returns: (success: bool, results: List[Object])
        """
        directive, content = parse_line(line)
        if directive is None:  # Empty line or comment
            return True, []
        # Intercept Using directive for import handling
        if directive == "Using":
            if not content:
                return False, [Term("Error", data={"result": "Using requires filename"})]
            return self.importer.handle(content[0].symbol)
        return self.pipeline.process(directive, content)

    def undo(self) -> bool:
        """Undo last state change. Returns False if nothing to undo."""
        return self.pipeline.undo()

    def breakpoint(self, name: str) -> None:
        """Create named breakpoint for rollback."""
        self.pipeline.breakpoint(name)

    def rollback(self, name: str) -> bool:
        """Rollback to named breakpoint. Returns False if not found."""
        return self.pipeline.rollback(name)

    def set_base_path(self, path) -> None:
        """Set the base path for resolving imports."""
        self.importer.set_base_path(path)
