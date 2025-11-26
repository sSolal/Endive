"""
Build Helper

Manages objects building.
"""

from typing import Tuple, List
from dataclasses import replace
from .helper import Helper, hookify
from ...core import Object, check, reduce


class BuildHelper(Helper):
    """
    Manages objects building.
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_handler('Check', self.handle_check)
        self.register_handler('Reduce', self.handle_reduce)

    @hookify
    def handle_check(self, directive: str, obj: Object) -> Tuple[bool, List[Object]]:
        success, message = check(obj)
        return success, [replace(obj, data={**obj.data, "result": message})]

    @hookify
    def handle_reduce(self, directive: str, obj: Object) -> Tuple[bool, List[Object]]:
        reduced = reduce(obj)
        return True, [reduced]
