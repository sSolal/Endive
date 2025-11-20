"""
Alias Helper

Manages name-to-term substitutions (aliases).

According to THOUGHTS.md:
- State: Aliases (dict of names to terms)
- Hooks:
  - ALL: Replace aliases in terms
  - Axiom/Definition/Canonical/Computational/Lemma: Extract name and add to aliases
"""

from typing import List, Tuple, Dict
from .helper import Helper
from ...core import Object



class AliasHelper(Helper):
    """
    Manages aliases (name-to-term substitutions).

    Hooks:
    - ALL directives: Substitute aliases in terms
    Handler:
    - Define name, object : Add an alias
    """

    def __init__(self) -> None:
        super().__init__()
        self.aliases: Dict[str, Object] = {}
        self.register_hook(['ALL'], self.all_hook)
        self.register_handler('Define', self.define_handler)

    def all_hook(self, *arguments: Object) -> List[Object]:
        return [self.apply_aliases(arg) for arg in arguments]

    def apply_aliases(self, argument: Object) -> Object:
        if argument.type == 'Term' and len(argument.children) == 0 and argument.handle in self.aliases:
            return self.aliases[argument.handle]
        else:
            new_children = tuple(self.apply_aliases(child) for child in argument.children)
            return Object(argument.type, new_children, argument.handle, argument.repr_func, argument.data)

    def define_handler(self, name: Object, obj: Object) -> Tuple[bool, str]:
        if name.type != 'Term' or len(name.children) != 0:
            return False, "Name must be a simple term with no arguments"
        self.aliases[name.handle] = obj
        return True, name.handle + " defined"