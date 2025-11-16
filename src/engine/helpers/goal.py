"""
Goal Helper

Manages usability directives
"""

from .helper import Helper
from ...core import Object, check, reduce


class GoalHelper(Helper):
    """
    Manages goals, context, and term building.
    """

    def __init__(self):
        super().__init__()
        self.register_handler('Check', self.handle_check)
        self.register_handler('Reduce', self.handle_reduce)
    def handle_check(self, argument):
        return check(argument)

    def handle_reduce(self, argument):
        return True, str(reduce(argument))