"""
Peano Helper
Manages bidirectional conversion between integer notation and Peano encoding.
- Forhook: Converts integer strings (e.g., "3", "0") to Peano encoding (S(S(S(zero))), zero)
- Backhook: Converts Peano encodings back to integer strings
"""

from typing import List, Tuple
from .helper import Helper, hookify
from ...core import Object, Term


class PeanoHelper(Helper):
    """
    Manages Peano encoding conversions.

    Forhook: Replace integer strings with Peano encoding
    Backhook: Replace Peano encoding with integer strings
    """

    def __init__(self) -> None:
        super().__init__()
        self.register_hook(['ALL'], self.all_forhook, self.all_backhook)

    @hookify
    def all_forhook(self, directive: str, *arguments: Object) -> List[Object]:
        """Forhook: convert integer strings to Peano encoding"""
        return [self.integer_to_peano(arg) for arg in arguments]

    def integer_to_peano(self, argument: Object) -> Object:
        """Recursively convert integer strings to Peano encoding"""
        # Base case: Term with integer string handle and no children
        if argument.type == 'Term' and len(argument.children) == 0:
            if argument.handle and argument.handle.isdigit():
                n = int(argument.handle)
                # Build S(S(...S(zero)...))
                result = Term("zero", ())
                for _ in range(n):
                    result = Term("S", (result,))
                # Preserve data
                return Object(result.type, result.children, result.handle,
                            result.repr_func, dict(argument.data))

        # Recursive case: transform children
        new_children = tuple(self.integer_to_peano(child) for child in argument.children)
        return Object(argument.type, new_children, argument.handle,
                     argument.repr_func, dict(argument.data))

    @hookify
    def all_backhook(self, directive: str, *results: Object) -> List[Object]:
        """Backhook: convert Peano encoding to integer strings"""
        return [self.peano_to_integer(result) for result in results]

    def peano_to_integer(self, argument: Object) -> Object:
        """Recursively convert Peano encoding to integer strings"""
        # Try to recognize ANY Peano pattern S(S(...zero...))
        # This converts ALL Peano encodings, not just those converted in forhook
        if argument.type == 'Term':
            if argument.handle == 'S' and len(argument.children) == 1:
                count, is_valid = self.count_peano_depth(argument)
                if is_valid:
                    # Replace with integer term
                    return Term(str(count), (), data=dict(argument.data))
            elif argument.handle == 'zero' and len(argument.children) == 0:
                return Term("0", (), data=dict(argument.data))

        # Recursive case
        new_children = tuple(self.peano_to_integer(child) for child in argument.children)
        return Object(argument.type, new_children, argument.handle,
                     argument.repr_func, dict(argument.data))

    def count_peano_depth(self, obj: Object) -> Tuple[int, bool]:
        """Returns (depth, is_valid_peano). Counts nested S() until reaching zero."""
        if obj.type == 'Term' and obj.handle == 'zero' and len(obj.children) == 0:
            return 0, True
        elif obj.type == 'Term' and obj.handle == 'S' and len(obj.children) == 1:
            inner_count, is_valid = self.count_peano_depth(obj.children[0])
            return (inner_count + 1, is_valid) if is_valid else (0, False)
        else:
            return 0, False
