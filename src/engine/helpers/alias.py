"""
Alias Helper

Manages name-to-term substitutions (aliases).

State: tuple of (name, Object) pairs
"""

from typing import List, Tuple, Dict, Optional
from dataclasses import replace
from .helper import Helper, hookify
from ...core import Object, Term

# Type alias: tuple of (name, object) pairs
AliasState = Tuple[Tuple[str, Object], ...]


def get_alias(state: AliasState, name: str) -> Optional[Object]:
    """Look up an alias by name in the state tuple"""
    for k, v in state:
        if k == name:
            return v
    return None


def with_alias(state: AliasState, name: str, obj: Object) -> AliasState:
    """Return new state with alias added/replaced"""
    return tuple((k, v) for k, v in state if k != name) + ((name, obj),)


class AliasHelper(Helper[AliasState]):
    """
    Manages aliases (name-to-term substitutions).

    State: tuple of (name, Object) pairs

    Forhooks:
    - ALL directives: Substitute aliases in terms, tag them with hash
    Backhooks:
    - ALL directives: Restore alias names if objects unchanged (hash matches)
    Handler:
    - Define name, object : Add an alias
    """

    def __init__(self) -> None:
        super().__init__(())  # Empty tuple as initial state
        self.register_hook(['ALL'], self.all_forhook, self.all_backhook)
        self.register_handler('Define', self.define_handler)

    @hookify
    def all_forhook(self, directive: str, *arguments: Object) -> List[Object]:
        """Forhook: replace aliases with definitions, tag them with hash"""
        return [self.apply_aliases(arg) for arg in arguments]

    def apply_aliases(self, argument: Object) -> Object:
        """Recursively apply aliases, tagging replacements with hash"""
        if argument.type == 'Term' and len(argument.children) == 0:
            expanded = get_alias(self.state, argument.handle)
            if expanded is not None:
                alias_name = argument.handle
                # Compute hash of expanded object (excluding data field)
                expanded_hash = hash(expanded)
                # Tag with alias metadata including hash
                new_data = {**expanded.data, "alias": alias_name, "alias_hash": expanded_hash}
                return Object(expanded.type, expanded.children, expanded.handle,
                             expanded.repr_func, new_data)

        new_children = tuple(self.apply_aliases(child) for child in argument.children)
        return Object(argument.type, new_children, argument.handle, argument.repr_func, dict(argument.data))

    @hookify
    def all_backhook(self, directive: str, *results: Object) -> List[Object]:
        """Backhook: restore alias names in results if objects unchanged"""
        return [self.restore_aliases(result) for result in results]

    def restore_aliases(self, obj: Object) -> Object:
        """Recursively restore aliases if object has alias tag AND is unchanged (hash matches)"""
        # If tagged with alias, check if object is unchanged
        if "alias" in obj.data and "alias_hash" in obj.data:
            alias_name = obj.data["alias"]
            stored_hash = obj.data["alias_hash"]

            # Compute current hash (excluding data field)
            current_hash = hash(obj)

            # Only restore if unchanged (hash matches)
            if current_hash == stored_hash:
                # Preserve data but remove alias-specific fields
                restored_data = {k: v for k, v in obj.data.items() if k not in ("alias", "alias_hash")}
                return Object("Term", (), alias_name, None, restored_data)
            # Otherwise, let the expanded/transformed version show through

        # Recursively process children
        if obj.children:
            new_children = tuple(self.restore_aliases(child) for child in obj.children)
            return Object(obj.type, new_children, obj.handle,
                         obj.repr_func, obj.data)

        return obj

    @hookify
    def define_handler(self, directive: str, name: Object, obj: Object) -> Tuple[bool, List[Object]]:
        if name.type != 'Term' or len(name.children) != 0:
            return False, [replace(name, data={**name.data, "result": "Name must be a simple term with no arguments"})]
        self.set_state(with_alias(self.state, name.handle, obj))
        return True, [replace(name, data={**name.data, "result": "[] defined"})]