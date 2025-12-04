"""
Functorial State Management

Stores functorial rewriting rules indexed by (inner_rew, term_symbol, position).
State: tuple of (key, value) pairs where:
  - key: (inner_rew_symbol, term_symbol, position_index)
  - value: (outer_rew_symbol, functorial_rule_object)
"""

from typing import Tuple, Optional
from ....core import Object

# Type aliases
FunctorialKey = Tuple[str, str, int]  # (inner_rew, term_symbol, position)
FunctorialValue = Tuple[str, Object]  # (outer_rew, rule)
FunctorialState = Tuple[Tuple[FunctorialKey, FunctorialValue], ...]


def get_functorial(state: FunctorialState, inner_rew: str, term_symbol: str,
                   position: int) -> Optional[FunctorialValue]:
    """Look up a functorial rule by key"""
    key = (inner_rew, term_symbol, position)
    for k, v in state:
        if k == key:
            return v
    return None


def add_functorial(state: FunctorialState, inner_rew: str, term_symbol: str,
                    position: int, outer_rew: str, rule: Object) -> FunctorialState:
    """Return new state with functorial rule added/replaced"""
    key = (inner_rew, term_symbol, position)
    value = (outer_rew, rule)
    return tuple((k, v) for k, v in state if k != key) + ((key, value),)
