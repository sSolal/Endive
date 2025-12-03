from typing import Optional
from .objects import Object


def get_hole_names(term: Object) -> set[str]:
    if term.type == "Hole":
        return {term.handle}
    result = set()
    for child in term.children:
        result.update(get_hole_names(child))
    return result


def extract_integer(obj: Object) -> Optional[int]:
    if obj.type != 'Term':
        return None
    if len(obj.children) == 0 and obj.handle and obj.handle.isdigit():
        return int(obj.handle)

    # Check if it's Peano encoded (S(S(...(zero)...)))
    if obj.handle == 'zero' and len(obj.children) == 0:
        return 0
    elif obj.handle == 'S' and len(obj.children) == 1:
        inner_val = extract_integer(obj.children[0])
        if inner_val is not None:
            return inner_val + 1

    return None