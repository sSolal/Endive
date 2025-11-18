"""
Build Helper

Manages objects building.
"""

from .helper import Helper
from ...core import check, reduce


class BuildHelper(Helper):
    """
    Manages objects building.
    """

    def __init__(self):
        super().__init__()
        self.register_handler('Check', self.handle_check)
        self.register_handler('Reduce', self.handle_reduce)

    def handle_check(self, object):
        return check(object)

    def handle_reduce(self, object):
        return True, str(reduce(object))
