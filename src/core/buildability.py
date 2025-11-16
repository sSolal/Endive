"""
Core Buildability Checker

This module contains the core logic for checking if terms are buildable
based on inductive definitions.

Buildability Rules:
1. Terms in context are buildable (axioms)
2. Applications are buildable if both parts are buildable
3. Rules are buildable if result is buildable with pattern added to context
"""

from .objects import Rew, Comp, Hole

def dict_add(dict, key, value):
    if key not in dict:
        dict[key] = []
    dict[key].append(value)
    return dict

def check(term, rule = None, context = {}):
    if rule in context and term in context[rule]:
        return True, str(term) + " in context"
    elif term.type == "Rew":
        return check(term.right, term.symbol, dict_add(context, term.symbol, term.left))
    elif term.type == "Comp":
        res,mes = check(term.left, rule, context) 
        if not res:
            return False, mes
        res, mes = check(term.right, rule, context)
        if not res:
            return False, mes
        return True, ""
    return False, str(term) + " is not buildable"
