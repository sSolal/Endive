"""
Alias Helper

Manages name-to-term substitutions (aliases).

According to THOUGHTS.md:
- State: Aliases (dict of names to terms)
- Hooks:
  - ALL: Replace aliases in terms
  - Axiom/Definition/Canonical/Computational/Lemma: Extract name and add to aliases
"""

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

    def __init__(self):
        super().__init__()
        self.aliases = {}
        self.register_hook(['ALL'], self.all_hook)
        self.register_handler('Define', self.define_handler)

    def all_hook(self, *arguments):
        return [self.apply_aliases(arg) for arg in arguments]

    def apply_aliases(self, argument):
        if argument.type == 'Term' and len(argument.children) == 0 and argument.handle in self.aliases:
            return self.aliases[argument.handle]
        else:
            return Object(argument.type, [self.apply_aliases(child) for child in argument.children], argument.handle, argument.repr)

    def define_handler(self, name, object):
        if name.type != 'Term' or len(name.children) != 0:
            return False, "Name must be a simple term with no arguments"
        self.aliases[name.handle] = object
        return True, name.handle + " defined"