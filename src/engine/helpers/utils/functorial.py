"""
Functorial State Management

Stores functorial rewriting rules indexed by (inner_rew, term_symbol, position).
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
from ....core import Object


@dataclass
class FunctorialState:
    """Manages functorial rewriting rules"""

    # Key: (inner_rew_symbol, term_symbol, position_index)
    # Value: (outer_rew_symbol, functorial_rule_object)
    functorial_rules: Dict[Tuple[str, str, int], Tuple[str, Object]] = field(default_factory=dict)

    def add_functorial(self, inner_rew: str, term_symbol: str, position: int,
                       outer_rew: str, rule: Object) -> None:
        key = (inner_rew, term_symbol, position)
        self.functorial_rules[key] = (outer_rew, rule)

    def get_functorial(self, inner_rew: str, term_symbol: str, position: int) -> Optional[Tuple[str, Object]]:
        key = (inner_rew, term_symbol, position)
        return self.functorial_rules.get(key)
