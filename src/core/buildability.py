"""
Core Buildability Checker

This module contains the core logic for checking if terms are buildable
based on inductive definitions.

Buildability Rules:
1. Terms in context are buildable (axioms)
2. Applications are buildable if both parts are buildable
3. Rules are buildable if result is buildable with the reduced pattern added to context
"""

from typing import Dict, List, Optional, Tuple
from .objects import Object, Rew, Comp, Hole
from .operations import reduce

def dict_add(d: Dict[str, List[Object]], key: str, value: Object) -> Dict[str, List[Object]]:
    if key not in d:
        d[key] = []
    d[key].append(value)
    return d

def check(obj: Object, rule: Optional[str] = None, context: Optional[Dict[str, List[Object]]] = None) -> Tuple[bool, str]:
    """Checks if an object is buildable according to the inductive definition."""
    if context is None:
        context = {}
    if rule in context and obj in context[rule]:
        return True, str(obj) + " in context"
    elif obj.type == "Rew":
        return check(obj.right, obj.symbol, dict_add(dict(context), obj.symbol, reduce(obj.left)))
    elif obj.type == "Comp":
        res, mes = check(obj.left, rule, context)
        if not res:
            return False, mes
        res, mes = check(obj.right, rule, context)
        if not res:
            return False, mes
        return True, ""
    return False, str(obj) + " is not buildable"
