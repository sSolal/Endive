"""
Proof Assistant (New Pipeline Architecture)

This engine takes a line of text, parses it, processes it through the pipeline, and returns the diagnoses in displayed format
"""

from typing import Tuple, List
from .pipeline import Pipeline
from ..core import Object
from .helpers import (
    PeanoHelper,
    AliasHelper,
    GoalHelper,
    BuildHelper
)
from .parser import parse_line, ParseError
import re


class Engine:
    """

    The proof assistant maintains a pipeline of helpers that process directives.
    Each helper can hook into directives for pre-processing and/or handle them fully.

    The flow is:
    Directive + Term -> Pipeline (Hooks -> Handler) -> Terms + Diagnoses
    """

    def __init__(self) -> None:
        self.pipeline = Pipeline()

        # Register helpers in order
        # Order matters for hooks! They are applied in registration order.

        # 1. Peano helper (should run first to convert integers to/from Peano)
        self.peano_helper = PeanoHelper()
        self.pipeline.helpers.append(self.peano_helper)

        # 2. Alias helper (should run after Peano to substitute names)
        self.alias_helper = AliasHelper()
        self.pipeline.helpers.append(self.alias_helper)

        # Goal helper, should handle most directives
        self.goal_helper = GoalHelper()
        self.pipeline.helpers.append(self.goal_helper)

        # Build helper, should handle building objects
        self.build_helper = BuildHelper()
        self.pipeline.helpers.append(self.build_helper)

    def process(self, line: str) -> Tuple[bool, List[Object]]:
        """
        Check a single line of proof using the pipeline.
        Returns: (success: bool, results: List[Object])
        """
        # Parse the line
        directive, content = parse_line(line)

        if directive is None:  # Empty line or comment
            return True, []

        return self.pipeline.process(directive, content)
