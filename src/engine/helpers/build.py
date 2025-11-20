"""
Build Helper

Manages objects building.
"""

from typing import Tuple
from .helper import Helper
from ...core import Object, check, reduce


class BuildHelper(Helper):
    """
    Manages objects building.
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_handler('Check', self.handle_check)
        self.register_handler('Reduce', self.handle_reduce)

    def handle_check(self, obj: Object) -> Tuple[bool, str]:
        return check(obj)

    def handle_reduce(self, obj: Object) -> Tuple[bool, str]:
        return True, str(reduce(obj))
